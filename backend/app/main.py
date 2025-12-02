# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import List, Dict, Any
from pathlib import Path
from fastapi.staticfiles import StaticFiles
import json
import os

from .database import engine, create_db_and_tables, DATABASE_URL
from .models import Question, Reponse
from . import llm

app = FastAPI(title="RAG GLPI avec Ollama + Mistral")

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

def get_session():
    with Session(engine) as session:
        yield session


class AskRequest(BaseModel):
    user_ad_id: int
    question: str

@app.get("/glpi/stats")
def get_glpi_stats():
    """Retourne des statistiques sur les données GLPI mockées"""
    from .glpi_mock import glpi_mock
    return {
        "tickets_count": len(glpi_mock.tickets),
        "kb_articles_count": len(glpi_mock.kb_articles),
        "faq_items_count": len(glpi_mock.faq_items),
        "total_entries": len(glpi_mock.tickets) + len(glpi_mock.kb_articles) + len(glpi_mock.faq_items)
    }

@app.get("/glpi/preview/{source_type}")
def preview_glpi_data(source_type: str):
    """Aperçu des données GLPI par type (tickets, kb_articles, faq)"""
    from .glpi_mock import glpi_mock
    
    if source_type == "tickets":
        return {"data": glpi_mock.tickets[:3]}  # 3 premiers tickets
    elif source_type == "kb_articles":
        return {"data": glpi_mock.kb_articles}
    elif source_type == "faq":
        return {"data": glpi_mock.faq_items}
    else:
        raise HTTPException(status_code=404, detail="Type de source inconnu")

@app.post("/ask/")
def ask_question(request: AskRequest, session: Session = Depends(get_session)):
    """
    Endpoint principal: pose une question avec RAG sur données GLPI
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
            embedding_question=embedding_to_store
        )
        session.add(db_question)
        session.commit()
        session.refresh(db_question)

        # Utiliser RAG avec GLPI mock au lieu de la réponse directe
        llm_response, sources = llm.get_rag_response(request.question)

        db_reponse = Reponse(
            reponse_label=llm_response,
            question_id=db_question.id
        )
        session.add(db_reponse)
        session.commit()
        session.refresh(db_reponse)

        return {
            "question": db_question.question_label,
            "answer": db_reponse.reponse_label,
            "sources": sources  # Ajout des sources GLPI utilisées
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Monter le frontend en dernier pour servir les fichiers statiques
# Dans Docker, le frontend est à /app/frontend
frontend_path = Path("/app/frontend") if Path("/app/frontend").exists() else Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")