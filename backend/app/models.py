import os
from typing import Any
from typing import List
from typing import Optional

from sqlalchemy import Text
from sqlmodel import Column, Field, Relationship, SQLModel

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rag_database.db")
if "postgresql" in DATABASE_URL:
    from pgvector.sqlalchemy import Vector
    embedding_column = Column(Vector(768))
else:
    embedding_column = Column(Text)


class Technicien(SQLModel, table=True):
    """Table des techniciens avec leurs domaines d'expertise."""

    id: Optional[int] = Field(default=None, primary_key=True)
    nom: str = Field(unique=True, index=True)
    email: str
    description: Optional[str] = None

    reponses: List["Reponse"] = Relationship(back_populates="technicien")


class Reponse(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    reponse_label: str
    validite: Optional[int] = Field(default=0)
    nombre_resolution: Optional[int] = Field(default=0)

    question_id: int = Field(foreign_key="question.id")
    question: "Question" = Relationship(back_populates="reponses")

    technicien_id: Optional[int] = Field(default=None, foreign_key="technicien.id")
    technicien: Optional["Technicien"] = Relationship(back_populates="reponses")


class Question(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    user_ad_id: int
    question_label: str
    embedding_question: Any = Field(sa_column=embedding_column)

    reponses: List[Reponse] = Relationship(back_populates="question")
