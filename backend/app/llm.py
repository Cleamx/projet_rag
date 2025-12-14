"""Module d'intégration avec Ollama pour LLM et embeddings."""
import re
from typing import Dict, List, Optional, Tuple

import ollama

from .glpi_mock import glpi_mock

client = ollama.Client(host="http://ollama:11434")
MODEL_NAME = "mistral"
EMBEDDING_MODEL_NAME = "nomic-embed-text"

# Catégories de techniciens disponibles pour la classification
TECHNICIEN_CATEGORIES = {
    "Techniciens": "Support technique général, assistance informatique DSIN",
    "Réseau": "Problèmes réseau, connexion internet, wifi, câblage",
    "Métier": "Applications métier, logiciels spécifiques aux services",
    "SharePoint": "SharePoint, sites collaboratifs, espaces de travail",
    "Exchange": "Exchange, Outlook, messagerie, calendrier, mail",
    "Campus numérique": "Services numériques du campus, outils pédagogiques",
    "Comptes": "Gestion des comptes utilisateurs, mots de passe, accès",
    "Cours en ligne": "Plateforme de cours en ligne, Moodle, e-learning",
    "Audiovisuel": "Équipements audiovisuels, visioconférence, projecteurs",
    "Copieurs": "Imprimantes, copieurs, photocopieuses Xerox",
    "Suivi de commande": "Suivi des commandes de matériel informatique",
}


def get_embedding(text: str) -> list[float]:
    """Génère un embedding vectoriel pour le texte donné.

    Args:
        text: Texte à vectoriser

    Returns:
        Liste de floats représentant l'embedding
    """
    response = client.embeddings(model=EMBEDDING_MODEL_NAME, prompt=text)
    return response["embedding"]


def get_chat_response(question: str) -> str:
    """Obtient une réponse directe du LLM.

    Args:
        question: Question à poser au modèle

    Returns:
        Réponse générée par le modèle
    """
    response = client.chat(
        model=MODEL_NAME, messages=[{"role": "user", "content": question}]
    )
    return response["message"]["content"]


def parse_category_from_response(response: str) -> Tuple[str, Optional[str]]:
    """Parse et extrait le tag de catégorie de la réponse LLM.

    Args:
        response: Réponse brute du LLM contenant potentiellement [CATEGORY:xxx]

    Returns:
        Tuple (réponse_nettoyée, catégorie) où catégorie peut être None
    """
    # Regex plus souple pour capturer [CATEGORY:xxx] ou [xxx] à la fin
    # On cherche un tag entre crochets contenant une des catégories connues
    pattern = r'\[(?:CATEGORY:)?\s*([^\]]+)\s*\]'
    match = re.search(pattern, response)

    if match:
        possible_category = match.group(1).strip()
        # Nettoyage de la réponse en enlevant tout ce qui ressemble au tag à la fin
        cleaned_response = re.sub(pattern, '', response).strip()
        
        # Vérification si le contenu du tag correspond à une catégorie connue (case insensitive)
        for cat_name in TECHNICIEN_CATEGORIES:
            if cat_name.lower() in possible_category.lower():
                return cleaned_response, cat_name

        return cleaned_response, None

    return response.strip(), None


def _build_categories_prompt() -> str:
    """Construit la partie du prompt listant les catégories disponibles."""
    lines = ["CATÉGORIES DE TECHNICIENS DISPONIBLES:"]
    for nom, description in TECHNICIEN_CATEGORIES.items():
        lines.append(f"- {nom}: {description}")
    return "\n".join(lines)


def get_rag_response(
    question: str, top_k: int = 4
) -> Tuple[str, List[Dict]]:
    """Génère une réponse en utilisant RAG avec similarité vectorielle pgvector.

    Args:
        question: Question de l'utilisateur
        top_k: Nombre de sources à récupérer

    Returns:
        Tuple (réponse_générée, sources_utilisées, catégorie_technicien)
    """
    
    # 1. Générer l'embedding de la question
    print(f"🔍 Génération de l'embedding pour: {question[:50]}...")
    question_embedding = get_embedding(question)
    
    # 2. Chercher dans PostgreSQL avec pgvector (solutions des techniciens)
    from .database import engine
    from sqlmodel import Session, text
    
    rag_results = []
    
    with Session(engine) as session:
        # Convertir embedding en format PostgreSQL vector
        embedding_str = "[" + ",".join(str(x) for x in question_embedding) + "]"
        
        # Requête SQL avec pgvector pour similarité cosine
        query = text("""
            SELECT 
                q.id,
                q.question_label,
                r.reponse_label,
                (q.embedding_question <=> :embedding::vector) AS distance
            FROM question q
            JOIN reponse r ON r.question_id = q.id
            WHERE r.reponse_label IS NOT NULL
            ORDER BY distance ASC
            LIMIT :limit
        """)
        
        try:
            results = session.execute(
                query,
                {"embedding": embedding_str, "limit": top_k}
            ).fetchall()
            
            print(f"✅ Recherche vectorielle: {len(results)} résultats trouvés dans le RAG")
            
            # Convertir les résultats en format exploitable
            for q_id, question_label, reponse_label, distance in results:
                similarity = 1 - float(distance)  # Convertir distance en similarité
                print(f"   - Question #{q_id}: similarité = {similarity:.2f}")
                
                rag_results.append({
                    "source": "question",
                    "id": q_id,
                    "title": question_label[:100],
                    "content": f"**Problème**: {question_label}\n\n**Solution**: {reponse_label}",
                    "metadata": {
                        "distance": float(distance),
                        "similarity": similarity
                    },
                    "score": similarity
                })
                
        except Exception as e:
            print(f"⚠️ Erreur recherche vectorielle: {e}")
            # Continue sans les résultats RAG
    
    # 3. Ajouter aussi les résultats de glpi_mock (données statiques)
    glpi_results = glpi_mock.search_all(question, limit=2)
    print(f"📚 Recherche glpi_mock: {len(glpi_results)} résultats trouvés")
    
    # 4. Combiner tous les résultats
    all_results = rag_results + glpi_results
    
    # 5. Trier par score (similarité) et limiter
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    all_results = all_results[:top_k]
    
    print(f"🎯 Total: {len(all_results)} sources retenues")
    
    # 6. Vérifier la pertinence des résultats
    SIMILARITY_THRESHOLD = 0.60  # Seuil minimum de 60%

    if not all_results:
        print("⚠️ Aucune source trouvée")
        return get_chat_response(question), []  # ←

    # Vérifier la similarité de la meilleure source
    best_score = all_results[0].get("score", 0)
    print(f"📊 Meilleure similarité trouvée: {best_score:.0%}")

    if best_score < SIMILARITY_THRESHOLD:
        print(f"⚠️ Similarité trop faible ({best_score:.0%} < {SIMILARITY_THRESHOLD:.0%})")
        print("   → Aucune bonne réponse disponible")
        # Retourner vide pour déclencher la création de ticket
        return "", []  # ← IMPORTANT : sources vides = ticket créé !
    
    # 7. Construire le contexte à partir des résultats
    context_parts = []
    sources = []
    
    for i, result in enumerate(all_results, 1):
        source_type = result['source'].upper()
        if result['source'] == 'question':
            source_type = "BASE RAG (Solution technicien)"
        
        context_parts.append(f"[Source {i} - {source_type}]")
        context_parts.append(f"Titre: {result['title']}")
        context_parts.append(result["content"])
        
        # Ajouter la similarité si disponible
        if "similarity" in result.get("metadata", {}):
            similarity = result["metadata"]["similarity"]
            context_parts.append(f"Pertinence: {similarity:.0%}")
        
        context_parts.append("\n---\n")
        
        sources.append({
            "type": result["source"],
            "id": result["id"],
            "title": result["title"],
            "metadata": result.get("metadata", {}),
        })
    
    context = "\n".join(context_parts)
    
    # 8. Générer la réponse avec Mistral
    categories_prompt = _build_categories_prompt()

    prompt = f"""Tu es un assistant IT helpdesk. Réponds à la question en \
utilisant UNIQUEMENT les informations fournies dans le contexte ci-dessous. \
Si l'information n'est pas dans le contexte, dis-le clairement.

CONTEXTE:
{context}

{categories_prompt}

QUESTION: {question}

RÉPONSE (sois concis et précis, cite les sources si pertinent):"""
    
    print("🤖 Génération de la réponse avec Mistral...")
    response = client.chat(
        model=MODEL_NAME, messages=[{"role": "user", "content": prompt}]
    )
    
    print("✅ Réponse générée avec succès")
    
    return response["message"]["content"], sources
INSTRUCTIONS:
1. Réponds de manière concise et précise, cite les sources si pertinent.
2. À LA FIN de ta réponse, ajoute un tag [CATEGORY:NomCatégorie] pour \
indiquer quel technicien devrait traiter cette question. Choisis la \
catégorie la plus appropriée parmi celles listées ci-dessus.

RÉPONSE:"""

    response = client.chat(
        model=MODEL_NAME, messages=[{"role": "user", "content": prompt}]
    )

    raw_response = response["message"]["content"]
    cleaned_response, category = parse_category_from_response(raw_response)

    return cleaned_response, sources, category

