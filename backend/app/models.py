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
