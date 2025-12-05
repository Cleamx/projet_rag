import json
from pathlib import Path

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session

from . import llm
from .database import DATABASE_URL
from .database import create_db_and_tables
from .database import engine
from .glpi_mock import glpi_mock
from .models import Question
from .models import Reponse

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


def get_session():
    with Session(engine) as session:
        yield session


class AskRequest(BaseModel):
    """Modèle de requête pour poser une question."""

    user_ad_id: int
    question: str


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

        llm_response, sources = llm.get_rag_response(request.question)

        db_reponse = Reponse(
            reponse_label=llm_response, question_id=db_question.id
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
