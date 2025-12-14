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
from .models import Technicien

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


class FeedbackRequest(BaseModel):
    """Modèle de requête pour le feedback."""

    response_id: int
    is_valid: bool


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


@app.post("/ask/")
def ask_question(
    request: AskRequest, session: Session = Depends(get_session)
):
    """Endpoint principal pour poser une question avec RAG.

    Args:
        request: Requête contenant user_ad_id et question
        session: Session SQLModel pour accès base de données

    Returns:
        Dict avec question, answer, response_id et sources

    Raises:
        HTTPException: En cas d'erreur serveur
    """
    try:
        embedding = llm.get_embedding(request.question)

        # Pour SQLite, sérialiser l'embedding en JSON
        embedding_to_store = embedding
        if "sqlite" in DATABASE_URL:
            embedding_to_store = json.dumps(embedding)

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
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback/")
def submit_feedback(
    request: FeedbackRequest, session: Session = Depends(get_session)
):
    """Endpoint pour soumettre un feedback sur une réponse.

    Args:
        request: Requête contenant response_id et is_valid
        session: Session SQLModel pour accès base de données

    Returns:
        Dict avec message de confirmation

    Raises:
        HTTPException: Si la réponse n'existe pas ou erreur serveur
    """
    try:
        db_reponse = session.get(Reponse, request.response_id)
        if not db_reponse:
            raise HTTPException(
                status_code=404, detail="Réponse non trouvée"
            )

        # Mise à jour de la validité (1 pour valide, -1 pour invalide)
        db_reponse.validite = 1 if request.is_valid else -1
        session.add(db_reponse)
        session.commit()

        return {
            "message": "Feedback enregistré avec succès",
            "response_id": request.response_id,
            "is_valid": request.is_valid,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
