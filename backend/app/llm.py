"""Module d'intégration avec Ollama pour LLM et embeddings."""
import os
import re

from typing import Dict, List, Optional, Tuple, Any


import ollama

from .config import settings
from .glpi_service import glpi_service
from .glpi_mock import glpi_mock


# Configuration du client Ollama local (pour LLM et embeddings)
ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
client = ollama.Client(host=ollama_host)

# Clé API Ollama pour la recherche web (service cloud ollama.com)
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

MODEL_NAME = "mistral"
EMBEDDING_MODEL_NAME = "nomic-embed-text"
GLPI_THRESHOLD = 0.5  # Seuil de pertinence pour basculer sur la recherche web

client = ollama.Client(host=settings.OLLAMA_HOST)

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
    """Génère un embedding vectoriel."""
    response = client.embeddings(model=settings.EMBEDDING_MODEL, prompt=text)
    return response["embedding"]


def get_chat_response(question: str) -> str:
    """Obtient une réponse directe du LLM."""
    response = client.chat(
        model=settings.MODEL_NAME,
        messages=[{"role": "user", "content": question}]
    )
    return response["message"]["content"]


def search_web(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """Effectue une recherche sur le web via l'API Ollama Web Search.

    Args:
        query: Requête de recherche
        max_results: Nombre maximum de résultats

    Returns:
        Liste de dictionnaires contenant les résultats
    """
    results = []
    
    if not OLLAMA_API_KEY:
        print("[Web Search] OLLAMA_API_KEY non configurée - recherche web désactivée")
        return results
    
    try:
        # Créer un client avec les headers d'authentification pour ollama.com
        web_client = ollama.Client(
            host="https://ollama.com",
            headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"}
        )
        
        # Appel à l'API web_search
        response = web_client.web_search(query=query, max_results=max_results)
        
        # Traitement des résultats
        web_results = response.results if hasattr(response, 'results') else []
        print(f"[Web Search] {len(web_results)} résultats trouvés pour: {query}")
        
        for i, r in enumerate(web_results):
            results.append({
                "source": "web",
                "id": f"web_{i+1}",
                "title": getattr(r, 'title', 'Sans titre'),
                "content": getattr(r, 'content', ''),
                "metadata": {
                    "url": getattr(r, 'url', ''),
                    "category": "Web"
                }
            })
    except Exception as e:
        print(f"[Web Search] Erreur lors de la recherche web: {e}")
    
    return results


def parse_category_from_response(response: str) -> Tuple[str, Optional[str]]:
    """Parse et extrait le tag de catégorie."""
    pattern = r'\[(?:CATEGORY:)?\s*([^\]]+)\s*\]'
    match = re.search(pattern, response)

    if match:
        possible_category = match.group(1).strip()
        cleaned_response = re.sub(pattern, '', response).strip()
        
        for cat_name in TECHNICIEN_CATEGORIES:
            if cat_name.lower() in possible_category.lower():
                return cleaned_response, cat_name

        return cleaned_response, None

    return response.strip(), None


def _build_categories_prompt() -> str:
    """Construit la partie du prompt listant les catégories."""
    lines = ["CATÉGORIES DE TECHNICIENS DISPONIBLES:"]
    for nom, description in TECHNICIEN_CATEGORIES.items():
        lines.append(f"- {nom}: {description}")
    return "\n".join(lines)


def get_rag_response(
    question: str, top_k: int = 4
) -> Tuple[str, List[Dict], Optional[str]]:
    """Génère une réponse en utilisant RAG avec GLPI ou le Web.

    Args:
        question: Question de l'utilisateur
        top_k: Nombre de sources à récupérer (pour GLPI)

    Returns:
        Tuple (réponse_générée, sources_utilisées, catégorie_technicien)
    """
    # 1. Recherche dans GLPI
    glpi_results = glpi_mock.search_all(question, limit=top_k)
    
    # 2. Vérification du score et décision de bascule vers Web
    use_web_search = False
    context_results = []
    source_type_label = "CONTEXTE GLPI"
    print(f"glpi_results: {glpi_results}")

    """Génère une réponse en utilisant RAG avec GLPI."""
    
    # Utiliser mock ou service réel selon config
    if settings.USE_MOCK:
        glpi_results = glpi_mock.search_all(question, limit=top_k)
    else:
        glpi_results = glpi_service.search_all(question, limit=top_k)

    if not glpi_results:
        use_web_search = True
    else:
        # Le premier résultat a le meilleur score (car trié)
        best_score = glpi_results[0].get("score", 0.0)
        print(f"Pertinence GLPI max: {best_score:.2f} < Threshold: {GLPI_THRESHOLD}")
        if best_score < GLPI_THRESHOLD:
            use_web_search = True
        else:
            context_results = glpi_results

    # 3. Exécution de la recherche Web si nécessaire
    if use_web_search:

        print(f"Pertinence GLPI trop faible (ou nulle) -> Bascule vers recherche Web (Threshold: {GLPI_THRESHOLD})")
        web_results = search_web(question, max_results=3)
        if web_results:
            context_results = web_results
            source_type_label = "CONTEXTE WEB"
        elif glpi_results:
            # Fallback sur GLPI si le web échoue mais qu'on avait des résultats (même faibles)
            context_results = glpi_results
            source_type_label = "CONTEXTE GLPI (Faible pertinence)"

    # Si aucun résultat nulle part (ni GLPI pertinent, ni Web), réponse directe
    if not context_results:
        raw_response = get_chat_response(question)
        cleaned, category = parse_category_from_response(raw_response)
        return cleaned, [], category

    # 4. Construction du contexte
    context_parts = []
    sources = []

    for i, result in enumerate(context_results, 1):
        source_name = result.get('source', 'unknown').upper()
        # Pour le web, on affiche l'URL si dispo
        if source_name == "WEB" and "url" in result.get("metadata", {}):
            source_info = f"{source_name} - {result['metadata']['url']}"
        else:
            source_info = source_name

        context_parts.append(f"[Source {i} - {source_info}]")
    # Construire le contexte
    context_parts = []
    sources = []

    for i, result in enumerate(glpi_results, 1):
        context_parts.append(f"[Source {i} - {result['source'].upper()}]")
        context_parts.append(f"Titre: {result['title']}")
        context_parts.append(result["content"])
        context_parts.append("\n---\n")

        sources.append({
            "type": result["source"],
            "id": result["id"],
            "title": result["title"],
            "metadata": result["metadata"],
        })

    context = "\n".join(context_parts)
    categories_prompt = _build_categories_prompt()

    prompt = f"""Tu es un assistant IT helpdesk. Réponds à la question en \
utilisant UNIQUEMENT les informations fournies dans le contexte ci-dessous. \
Le contexte provient de : {source_type_label}.
Si l'information n'est pas dans le contexte, dis-le clairement.
utilisant UNIQUEMENT les informations fournies dans le contexte ci-dessous.

{source_type_label}:
{context}

{categories_prompt}

QUESTION: {question}

INSTRUCTIONS:
1. Réponds de manière concise et précise, cite les sources si pertinent.
2. Si le contexte vient du WEB, précise-le dans ta réponse.
3. À LA FIN de ta réponse, ajoute un tag [CATEGORY:NomCatégorie] pour \
indiquer quel technicien devrait traiter cette question. Choisis la \
catégorie la plus appropriée parmi celles listées ci-dessus.
2. À LA FIN de ta réponse, ajoute un tag [CATEGORY:NomCatégorie].

RÉPONSE:"""

    response = client.chat(
        model=settings.MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_response = response["message"]["content"]
    cleaned_response, category = parse_category_from_response(raw_response)

    return cleaned_response, sources, category