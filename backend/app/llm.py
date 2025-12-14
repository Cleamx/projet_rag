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
) -> Tuple[str, List[Dict], Optional[str]]:
    """Génère une réponse en utilisant RAG avec GLPI.

    Args:
        question: Question de l'utilisateur
        top_k: Nombre de sources à récupérer

    Returns:
        Tuple (réponse_générée, sources_utilisées, catégorie_technicien)
    """
    glpi_results = glpi_mock.search_all(question, limit=top_k)

    if not glpi_results:
        raw_response = get_chat_response(question)
        cleaned, category = parse_category_from_response(raw_response)
        return cleaned, [], category

    # Construire le contexte à partir des résultats GLPI
    context_parts = []
    sources = []

    for i, result in enumerate(glpi_results, 1):
        context_parts.append(
            f"[Source {i} - {result['source'].upper()}]"
        )
        context_parts.append(f"Titre: {result['title']}")
        context_parts.append(result["content"])
        context_parts.append("\n---\n")

        sources.append(
            {
                "type": result["source"],
                "id": result["id"],
                "title": result["title"],
                "metadata": result["metadata"],
            }
        )

    context = "\n".join(context_parts)
    categories_prompt = _build_categories_prompt()

    prompt = f"""Tu es un assistant IT helpdesk. Réponds à la question en \
utilisant UNIQUEMENT les informations fournies dans le contexte ci-dessous. \
Si l'information n'est pas dans le contexte, dis-le clairement.

CONTEXTE GLPI:
{context}

{categories_prompt}

QUESTION: {question}

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

