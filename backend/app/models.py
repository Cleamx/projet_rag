from typing import List, Optional, Any
import os
from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import Text

# Import conditionnel de pgvector (seulement si PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rag_database.db")
if "postgresql" in DATABASE_URL:
    from pgvector.sqlalchemy import Vector
    # nomic-embed-text génère des embeddings de 768 dimensions
    embedding_column = Column(Vector(768))
else:
    # Pour SQLite, on stocke l'embedding en JSON/Text
    embedding_column = Column(Text)


class Reponse(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reponse_label: str
    validite: Optional[int] = Field(default=0)
    nombre_resolution: Optional[int] = Field(default=0)

    question_id: int = Field(foreign_key="question.id")
    question: "Question" = Relationship(back_populates="reponses")


class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_ad_id: int
    question_label: str
    embedding_question: Any = Field(sa_column=embedding_column)

    reponses: List[Reponse] = Relationship(back_populates="question")
