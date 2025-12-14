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
    tickets: List["GLPITicket"] = Relationship(back_populates="question")

#===========================================
#Stockage des tickets GLPI
#============================================
from datetime import datetime
#Créer une table dans PostgreSQL pour sauvegarder tous les tickets créés.
class GLPITicket(SQLModel, table=True):
    """Représente un ticket créé dans GLPI"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    glpi_ticket_id: Optional[int] = None  # ID du ticket dans GLPI réel
    
    # Utilisateur ayant créé le ticket
    user_ad_id: int # qui a creer le ticket
    question_id: Optional[int] = Field(foreign_key="question.id", default=None) #lié a quelle question
    
    # Informations du ticket
    title: str # problème VPN, imprimante, etc.
    description: str # je ne peux pas me connecter au vpn, l'imprimante ne fonctionne pas, etc.
    category: Optional[str] = None  # Réseau, Matériel, Logiciel, etc.
    priority: str = Field(default="Moyenne")  # Basse, Moyenne, Haute, Urgente
    status: str = Field(default="Nouveau")  # Nouveau, En cours, Résolu, Fermé
    
    # Réponse du technicien
    technician_name: Optional[str] = None
    technician_email: Optional[str] = None
    solution: Optional[str] = None
    
    # Dates
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    
    # Retrouver la question originale depuis le ticket
    # Voir tous les tickets créés pour une question
    # sans Relation # Il faudrait chercher par description (pas fiable !)
    #Suggérer des solutions existantes avant de créer un ticket
    # evite la creation d'un nouv ticket en cas de question similaire
    # Relation
    question: Optional["Question"] = Relationship(back_populates="tickets")
    