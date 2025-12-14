import json
from pathlib import Path

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select

from . import llm
from .database import DATABASE_URL
from .database import create_db_and_tables
from .database import engine
from .glpi_mock import glpi_mock
from .init_techniciens import get_technicien_by_nom, init_techniciens
from .models import Question
from .models import Reponse
from .models import GLPITicket

from datetime import datetime
from typing import List, Optional
from sqlmodel import select, func

from .clustering import determine_category, get_technician_email, get_priority
from .glpi_connector import glpi_connector, is_glpi_enabled
import logging
import os

logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG GLPI avec Ollama + Mistral",
    docs_url=None,
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    init_techniciens()


def get_session():
    with Session(engine) as session:
        yield session


class AskRequest(BaseModel):
    """Modèle de requête pour poser une question."""
    user_ad_id: int
    question: str


class CreateTicketRequest(BaseModel):
    """Requête pour créer un ticket GLPI"""
    user_ad_id: int
    question_id: Optional[int] = None
    title: str
    description: str


class TicketResponse(BaseModel):
    """Réponse avec les informations d'un ticket"""
    id: int
    title: str
    description: str
    category: str
    priority: str
    status: str
    technician_email: Optional[str] = None
    technician_name: Optional[str] = None
    solution: Optional[str] = None
    created_at: str
    resolved_at: Optional[str] = None


class GLPIWebhookRequest(BaseModel):
    """Requête webhook quand un technicien résout un ticket"""
    ticket_id: int
    technician_name: str
    technician_email: Optional[str] = None
    solution: str
    status: str = "Résolu"


# ============================================
# ENDPOINTS GLPI MOCK
# ============================================

@app.get("/glpi/preview/{source_type}")
def preview_glpi_data(source_type: str):
    """Aperçu des données GLPI par type.

    Args:
        source_type: Type de source (tickets, kb_articles, faq)

    Returns:
        Dict contenant les données demandées

    Raises:
        HTTPException: Si le type de source est inconnu
    """
    if source_type == "tickets":
        return {"data": glpi_mock.tickets[:3]}
    elif source_type == "kb_articles":
        return {"data": glpi_mock.kb_articles}
    elif source_type == "faq":
        return {"data": glpi_mock.faq_items}
    else:
        raise HTTPException(
            status_code=400, detail="Type de source inconnu"
        )


# ============================================
# ENDPOINT PRINCIPAL RAG
# ============================================

@app.post("/ask/")
def ask_question(
    request: AskRequest, session: Session = Depends(get_session)
):
    """Endpoint principal pour poser une question avec RAG.
    
    Workflow:
    1. Génère l'embedding de la question
    2. Sauvegarde la question en base
    3. Cherche dans le RAG (glpi_mock + historique)
    4. Si pas de sources trouvées → Crée automatiquement un ticket
    5. Génère une réponse (avec ou sans contexte)
    6. Sauvegarde la réponse

    Args:
        request: Requête contenant user_ad_id et question
        session: Session SQLModel pour accès base de données

    Returns:
        Dict avec question, answer, response_id, sources, et ticket_created

    Raises:
        HTTPException: En cas d'erreur serveur
    """
    try:
        # 1. Générer l'embedding de la question
        embedding = llm.get_embedding(request.question)

        # Pour SQLite, sérialiser l'embedding en JSON
        embedding_to_store = embedding
        if "sqlite" in DATABASE_URL:
            embedding_to_store = json.dumps(embedding)

        # 2. Sauvegarder la question en base
        db_question = Question(
            user_ad_id=request.user_ad_id,
            question_label=request.question,
            embedding_question=embedding_to_store,
        )
        session.add(db_question)
        session.commit()
        session.refresh(db_question)

        llm_response, sources, category = llm.get_rag_response(request.question)

        # Récupérer le technicien correspondant à la catégorie
        technicien_id = None
        if category:
            technicien = session.exec(
                select(Technicien).where(Technicien.nom == category)
            ).first()
            if technicien:
                technicien_id = technicien.id

        # 4. 🔥 Si pas de sources, créer un ticket automatiquement
        ticket_created = False
        ticket_id = None
        glpi_ticket_id = None
        
        if not sources or len(sources) == 0:
            logger.info(f"📋 Pas de sources trouvées pour la question. Création d'un ticket automatique...")
            
            # Déterminer catégorie et priorité
            category = determine_category(request.question)
            priority = get_priority(request.question)
            technician_email = get_technician_email(category)
            
            # Créer le ticket en base locale
            ticket = GLPITicket(
                user_ad_id=request.user_ad_id,
                question_id=db_question.id,
                title=request.question[:100],  # Limite à 100 caractères
                description=request.question,
                category=category,
                priority=priority,
                status="Nouveau",
                technician_email=technician_email
            )
            
            # 🔥 Créer aussi dans GLPI réel si configuré
            if is_glpi_enabled():
                try:
                    glpi_ticket_id = glpi_connector.create_ticket(
                        title=ticket.title,
                        description=ticket.description,
                        user_id=request.user_ad_id,
                        category=category,
                        priority=priority
                    )
                    
                    if glpi_ticket_id > 0:
                        ticket.glpi_ticket_id = glpi_ticket_id
                        logger.info(f"✅ Ticket GLPI #{glpi_ticket_id} créé automatiquement")
                except Exception as e:
                    logger.error(f"❌ Erreur création ticket GLPI réel : {e}")
                    # Continue quand même, le ticket est en base locale
            
            session.add(ticket)
            session.commit()
            session.refresh(ticket)
            
            ticket_created = True
            ticket_id = ticket.id
            
            # Modifier la réponse du LLM
            glpi_msg = f" (GLPI #{glpi_ticket_id})" if glpi_ticket_id else ""
            llm_response = f"""Je n'ai pas trouvé de solution dans ma base de connaissances pour cette question.

✅ J'ai automatiquement créé un ticket #{ticket.id}{glpi_msg} qui a été assigné à l'équipe **{category}** ({technician_email}).

**Priorité** : {priority}

Un technicien vous répondra dans les plus brefs délais. Vous pouvez suivre l'état de votre ticket via l'onglet "Mes tickets"."""

            logger.info(f"✅ Ticket #{ticket.id} créé automatiquement pour user {request.user_ad_id}")

        # 5. Sauvegarder la réponse
        db_reponse = Reponse(
            reponse_label=llm_response,
            question_id=db_question.id,
            technicien_id=technicien_id,
        )
        session.add(db_reponse)
        session.commit()
        session.refresh(db_reponse)

        return {
            "question": db_question.question_label,
            "answer": db_reponse.reponse_label,
            "response_id": db_reponse.id,
            "sources": sources,
            "ticket_created": ticket_created,
            "ticket_id": ticket_id,
            "glpi_ticket_id": glpi_ticket_id
        }

    except Exception as e:
        session.rollback()
        logger.error(f"❌ Erreur dans /ask/ : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS GESTION TICKETS
# ============================================

@app.post("/glpi/create-ticket")
def create_glpi_ticket(
    request: CreateTicketRequest,
    session: Session = Depends(get_session)
):
    """
    Crée un ticket GLPI (manuel ou automatique).
    
    Workflow:
    1. Détermine la catégorie automatiquement (clustering)
    2. Détermine la priorité selon les mots-clés
    3. Assigne le technicien approprié
    4. Crée le ticket en base locale
    5. 🔥 Crée le ticket dans GLPI réel si configuré
    
    Args:
        request: Données du ticket (user_ad_id, title, description)
        session: Session SQLModel
        
    Returns:
        Informations du ticket créé
        
    Raises:
        HTTPException: En cas d'erreur
    """
    
    try:
        # 1. Analyser le contenu pour déterminer catégorie et priorité
        full_text = f"{request.title} {request.description}"
        category = determine_category(full_text)
        priority = get_priority(full_text)
        technician_email = get_technician_email(category)
        
        # 2. Créer le ticket en base locale
        ticket = GLPITicket(
            user_ad_id=request.user_ad_id,
            question_id=request.question_id,
            title=request.title,
            description=request.description,
            category=category,
            priority=priority,
            status="Nouveau",
            technician_email=technician_email
        )
        
        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        
        # 3. 🔥 Créer aussi dans GLPI réel si configuré
        glpi_ticket_id = 0
        glpi_created = False
        
        if is_glpi_enabled():
            try:
                glpi_ticket_id = glpi_connector.create_ticket(
                    title=request.title,
                    description=request.description,
                    user_id=request.user_ad_id,
                    category=category,
                    priority=priority
                )
                
                if glpi_ticket_id > 0:
                    # Mettre à jour avec l'ID GLPI
                    ticket.glpi_ticket_id = glpi_ticket_id
                    session.commit()
                    glpi_created = True
                    logger.info(f"✅ Ticket créé dans GLPI réel : #{glpi_ticket_id}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur création GLPI réel : {e}")
                # Continue quand même, le ticket est en base locale
        
        return {
            "success": True,
            "ticket_id": ticket.id,
            "glpi_ticket_id": ticket.glpi_ticket_id,
            "glpi_created": glpi_created,
            "category": ticket.category,
            "priority": ticket.priority,
            "assigned_to": technician_email,
            "status": ticket.status,
            "message": f"Ticket créé avec succès. " + 
                      (f"Ticket GLPI #{glpi_ticket_id} créé." if glpi_created else f"Assigné à {category}.")
        }
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la création du ticket: {str(e)}"
        )


@app.get("/glpi/tickets/{user_ad_id}")
def get_user_tickets(
    user_ad_id: int, 
    session: Session = Depends(get_session)
):
    """
    Récupère tous les tickets d'un utilisateur.
    
    Args:
        user_ad_id: ID de l'utilisateur dans Active Directory
        session: Session SQLModel
        
    Returns:
        Liste des tickets de l'utilisateur
    """
    
    try:
        # Récupérer tous les tickets de l'utilisateur
        tickets = session.exec(
            select(GLPITicket)
            .where(GLPITicket.user_ad_id == user_ad_id)
            .order_by(GLPITicket.created_at.desc())
        ).all()
        
        return {
            "user_ad_id": user_ad_id,
            "total_tickets": len(tickets),
            "tickets": [
                {
                    "id": t.id,
                    "title": t.title,
                    "category": t.category,
                    "priority": t.priority,
                    "status": t.status,
                    "created_at": t.created_at.isoformat(),
                    "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
                    "has_solution": t.solution is not None,
                    "glpi_ticket_id": t.glpi_ticket_id
                }
                for t in tickets
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des tickets: {str(e)}"
        )


@app.get("/glpi/ticket/{ticket_id}")
def get_ticket_details(
    ticket_id: int,
    session: Session = Depends(get_session)
):
    """
    Récupère les détails complets d'un ticket.
    
    Args:
        ticket_id: ID du ticket
        session: Session SQLModel
        
    Returns:
        Détails complets du ticket
        
    Raises:
        HTTPException: Si le ticket n'existe pas
    """
    
    try:
        # Récupérer le ticket
        ticket = session.get(GLPITicket, ticket_id)
        
        if not ticket:
            raise HTTPException(
                status_code=404,
                detail=f"Ticket #{ticket_id} non trouvé"
            )
        
        return {
            "id": ticket.id,
            "glpi_ticket_id": ticket.glpi_ticket_id,
            "user_ad_id": ticket.user_ad_id,
            "question_id": ticket.question_id,
            "title": ticket.title,
            "description": ticket.description,
            "category": ticket.category,
            "priority": ticket.priority,
            "status": ticket.status,
            "technician_name": ticket.technician_name,
            "technician_email": ticket.technician_email,
            "solution": ticket.solution,
            "created_at": ticket.created_at.isoformat(),
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération du ticket: {str(e)}"
        )


@app.get("/glpi/stats")
def get_glpi_stats(session: Session = Depends(get_session)):
    """
    Statistiques globales sur les tickets GLPI.
    
    Returns:
        - Nombre total de tickets
        - Répartition par statut
        - Répartition par catégorie
        - Nombre d'entrées dans la base RAG
    """
    
    try:
        # Compte total des tickets
        total_tickets = session.exec(
            select(func.count(GLPITicket.id))
        ).one()
        
        # Répartition par statut
        status_query = session.exec(
            select(GLPITicket.status, func.count(GLPITicket.id))
            .group_by(GLPITicket.status)
        ).all()
        status_counts = {status: count for status, count in status_query}
        
        # Répartition par catégorie
        category_query = session.exec(
            select(GLPITicket.category, func.count(GLPITicket.id))
            .group_by(GLPITicket.category)
        ).all()
        category_counts = {cat: count for cat, count in category_query}
        
        # Tickets résolus vs non résolus
        resolved = session.exec(
            select(func.count(GLPITicket.id))
            .where(GLPITicket.status == "Résolu")
        ).one()
        
        # Nombre d'entrées dans la base RAG
        rag_entries = session.exec(
            select(func.count(Question.id))
        ).one()
        
        return {
            "total_tickets": total_tickets,
            "resolved_tickets": resolved,
            "pending_tickets": total_tickets - resolved,
            "by_status": status_counts,
            "by_category": category_counts,
            "rag_entries": rag_entries
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )


# ============================================
# WEBHOOK GLPI
# ============================================

@app.post("/glpi/webhook/ticket-resolved")
def glpi_ticket_resolved(
    request: GLPIWebhookRequest,
    session: Session = Depends(get_session)
):
    """
    🔥 WEBHOOK CRITIQUE : Appelé quand un technicien résout un ticket.
    
    Ce endpoint est LA CLÉ du système RAG évolutif :
    1. Met à jour le ticket (statut, solution, technicien)
    2. ALIMENTE LA BASE RAG avec la solution du technicien
    3. Génère l'embedding de la solution
    4. Les futures questions similaires trouveront cette réponse !
    
    Args:
        request: Données de résolution (ticket_id, solution, technicien)
        session: Session SQLModel
        
    Returns:
        Confirmation et IDs des entrées créées dans le RAG
        
    Raises:
        HTTPException: Si le ticket n'existe pas ou erreur
    """
    
    try:
        # 1. Trouver le ticket dans la base
        ticket = session.exec(
            select(GLPITicket).where(GLPITicket.id == request.ticket_id)
        ).first()
        
        if not ticket:
            raise HTTPException(
                status_code=404, 
                detail=f"Ticket #{request.ticket_id} non trouvé"
            )
        
        # 2. Mettre à jour le ticket avec la solution
        ticket.status = request.status
        ticket.technician_name = request.technician_name
        if request.technician_email:
            ticket.technician_email = request.technician_email
        ticket.solution = request.solution
        ticket.resolved_at = datetime.utcnow()
        
        # 3. 🔥 ALIMENTER LA BASE RAG
        # Construire un texte complet et structuré pour l'embedding
        rag_text = f"""Catégorie: {ticket.category}
Priorité: {ticket.priority}

Problème signalé:
{ticket.title}

Description détaillée:
{ticket.description}

Solution apportée par {request.technician_name}:
{request.solution}

Mots-clés: {ticket.category.lower()}, support, helpdesk, {ticket.title.lower()}
"""
        
        # 4. Générer l'embedding de cette solution
        logger.info(f"📊 Génération de l'embedding pour le ticket #{ticket.id}...")
        embedding = llm.get_embedding(rag_text)
        
        # 5. Sérialiser l'embedding pour SQLite si nécessaire
        embedding_to_store = embedding
        if "sqlite" in DATABASE_URL:
            embedding_to_store = json.dumps(embedding)
        
        # 6. Créer une nouvelle entrée Question dans la base RAG
        rag_question = Question(
            user_ad_id=ticket.user_ad_id,
            question_label=ticket.description,  # La question originale
            embedding_question=embedding_to_store
        )
        session.add(rag_question)
        session.flush()  # Pour obtenir l'ID sans committer
        
        # 7. Créer la Réponse associée
        rag_response = Reponse(
            reponse_label=request.solution,
            question_id=rag_question.id,
            validite=1,  # ✅ Validé par défaut (vient d'un technicien)
            nombre_resolution=0  # Sera incrémenté à chaque utilisation
        )
        session.add(rag_response)
        
        # 8. Créer un lien bidirectionnel (optionnel mais utile)
        ticket.question_id = rag_question.id
        
        # 9. Commit toutes les modifications
        session.commit()
        session.refresh(ticket)
        session.refresh(rag_question)
        session.refresh(rag_response)
        
        logger.info(f"✅ Ticket #{ticket.id} résolu et ajouté au RAG (Question #{rag_question.id})")
        
        return {
            "success": True,
            "message": "Ticket résolu et solution ajoutée à la base RAG",
            "ticket": {
                "id": ticket.id,
                "title": ticket.title,
                "category": ticket.category,
                "status": ticket.status,
                "resolved_at": ticket.resolved_at.isoformat()
            },
            "rag_entry": {
                "question_id": rag_question.id,
                "response_id": rag_response.id,
                "embedding_generated": True
            },
            "next_steps": "Les futures questions similaires trouveront automatiquement cette solution !"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Erreur lors du traitement du webhook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement: {str(e)}"
        )


# ============================================
# ENDPOINTS DE TEST
# ============================================

@app.post("/test/complete-workflow")
def test_complete_workflow(session: Session = Depends(get_session)):
    """
    🧪 Endpoint de test pour valider tout le workflow :
    1. Crée un ticket
    2. Le résout immédiatement
    3. Vérifie que la solution est dans le RAG
    4. Pose une question similaire
    
    Utilise cet endpoint pour tester que tout fonctionne !
    """
    
    try:
        # Étape 1 : Créer un ticket
        test_description = "Mon VPN ne se connecte plus, j'ai un message d'erreur timeout"
        test_title = "Problème connexion VPN"
        
        category = determine_category(f"{test_title} {test_description}")
        priority = get_priority(test_description)
        
        ticket = GLPITicket(
            user_ad_id=999,  # User de test
            title=test_title,
            description=test_description,
            category=category,
            priority=priority,
            status="Nouveau",
            technician_email=get_technician_email(category)
        )
        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        
        logger.info(f"✅ 1. Ticket #{ticket.id} créé (catégorie: {category})")
        
        # Étape 2 : Résoudre le ticket
        test_solution = """Le problème venait d'une mauvaise configuration du pare-feu. 
        
Procédure de résolution :
1. Ouvrir Windows Defender Firewall
2. Autoriser Cisco AnyConnect dans les exceptions
3. Redémarrer le service VPN
4. Tester la connexion

Le VPN fonctionne maintenant correctement."""
        
        webhook_data = GLPIWebhookRequest(
            ticket_id=ticket.id,
            technician_name="Jean Dupont (Test)",
            solution=test_solution,
            status="Résolu"
        )
        
        # Appeler le webhook
        result = glpi_ticket_resolved(webhook_data, session)
        
        logger.info(f"✅ 2. Ticket résolu et ajouté au RAG (Question #{result['rag_entry']['question_id']})")
        
        # Étape 3 : Tester la recherche RAG
        test_question = "J'ai un souci avec le VPN, ça ne marche pas"
        
        # Utiliser le RAG pour trouver la solution
        rag_answer, sources = llm.get_rag_response(test_question)
        
        logger.info(f"✅ 3. Question de test posée : '{test_question}'")
        logger.info(f"✅ 4. RAG a trouvé {len(sources)} source(s)")
        
        return {
            "success": True,
            "workflow": "Ticket créé → Résolu → Ajouté au RAG → Testé",
            "steps": {
                "1_ticket_created": {
                    "id": ticket.id,
                    "category": category,
                    "priority": priority
                },
                "2_ticket_resolved": result,
                "3_rag_tested": {
                    "test_question": test_question,
                    "sources_found": len(sources),
                    "answer_preview": rag_answer[:200] + "..."
                }
            },
            "conclusion": "✅ Workflow complet fonctionnel !" if sources else "⚠️ RAG n'a pas trouvé la solution"
        }
        
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/glpi/test-connection")
def test_glpi_connection():
    """Teste la connexion à GLPI réel"""
    
    if not is_glpi_enabled():
        return {
            "success": False,
            "message": "GLPI non configuré (tokens manquants)",
            "env_check": {
                "GLPI_API_URL": os.getenv("GLPI_API_URL", "NOT SET"),
                "GLPI_APP_TOKEN": "SET" if os.getenv("GLPI_APP_TOKEN") else "NOT SET",
                "GLPI_USER_TOKEN": "SET" if os.getenv("GLPI_USER_TOKEN") else "NOT SET"
            }
        }
    
    try:
        success = glpi_connector.test_connection()
        return {
            "success": success,
            "message": "✅ Connexion GLPI OK" if success else "❌ Connexion GLPI échouée",
            "glpi_url": os.getenv("GLPI_API_URL")
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Erreur : {str(e)}"
        }


# ============================================
# FRONTEND
# ============================================

frontend_path = (
    Path("/app/frontend")
    if Path("/app/frontend").exists()
    else Path(__file__).parent.parent.parent / "frontend"
)
if frontend_path.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(frontend_path), html=True),
        name="static",
    )
    