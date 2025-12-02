import ollama
from typing import List, Dict, Tuple
from .glpi_mock import glpi_mock

client = ollama.Client(host='http://ollama:11434')
MODEL_NAME = 'mistral'
EMBEDDING_MODEL_NAME = 'nomic-embed-text'

def get_embedding(text: str) -> list[float]:
    response = client.embeddings(model=EMBEDDING_MODEL_NAME, prompt=text)
    return response['embedding']

def get_chat_response(question: str) -> str:
    response = client.chat(
        model=MODEL_NAME,
        messages=[{'role': 'user', 'content': question}]
    )
    return response['message']['content']

def get_rag_response(question: str, top_k: int = 4) -> Tuple[str, List[Dict]]:
    """
    Génère une réponse en utilisant le RAG avec les données GLPI mockées.
    Retourne (réponse, sources_utilisées)
    """
    # Rechercher dans GLPI mock
    glpi_results = glpi_mock.search_all(question, limit=top_k)
    
    if not glpi_results:
        # Pas de contexte trouvé, réponse directe
        return get_chat_response(question), []
    
    # Construire le contexte à partir des résultats GLPI
    context_parts = []
    sources = []
    
    for i, result in enumerate(glpi_results, 1):
        context_parts.append(f"[Source {i} - {result['source'].upper()}]")
        context_parts.append(f"Titre: {result['title']}")
        context_parts.append(result['content'])
        context_parts.append("\n---\n")
        
        sources.append({
            "type": result['source'],
            "id": result['id'],
            "title": result['title'],
            "metadata": result['metadata']
        })
    
    context = "\n".join(context_parts)
    
    # Créer le prompt avec contexte
    prompt = f"""Tu es un assistant IT helpdesk. Réponds à la question en utilisant UNIQUEMENT les informations fournies dans le contexte ci-dessous. Si l'information n'est pas dans le contexte, dis-le clairement.

CONTEXTE GLPI:
{context}

QUESTION: {question}

RÉPONSE (sois concis et précis, cite les sources si pertinent):"""
    
    # Générer la réponse avec contexte
    response = client.chat(
        model=MODEL_NAME,
        messages=[{'role': 'user', 'content': prompt}]
    )
    
    return response['message']['content'], sources