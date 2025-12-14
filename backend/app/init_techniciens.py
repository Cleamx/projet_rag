"""Script pour initialiser la table des techniciens."""
from sqlmodel import Session, select

from .database import engine
from .models import Technicien


TECHNICIENS_DATA = [
    {
        "nom": "Techniciens",
        "email": "assistance.dsin@univ-corse.fr",
        "description": "Support technique général, assistance informatique DSIN",
    },
    {
        "nom": "Réseau",
        "email": "gerardeschi@univ-corse.fr",
        "description": "Problèmes réseau, connexion internet, wifi, câblage",
    },
    {
        "nom": "Métier",
        "email": "pole.metier@univ-corse.fr",
        "description": "Applications métier, logiciels spécifiques aux services",
    },
    {
        "nom": "SharePoint",
        "email": "sharepoint@univ-corse.fr",
        "description": "SharePoint, sites collaboratifs, espaces de travail",
    },
    {
        "nom": "Exchange",
        "email": "marechal-balle_a@univ-corse.fr",
        "description": "Exchange, Outlook, messagerie, calendrier, mail",
    },
    {
        "nom": "Campus numérique",
        "email": "assistance.campusnumerique@univ-corse.fr",
        "description": "Services numériques du campus, outils pédagogiques",
    },
    {
        "nom": "Comptes",
        "email": "assistance.comptes@univ-corse.fr",
        "description": "Gestion des comptes utilisateurs, mots de passe, accès",
    },
    {
        "nom": "Cours en ligne",
        "email": "assistance.coursenligne@univ-corse.fr",
        "description": "Plateforme de cours en ligne, Moodle, e-learning",
    },
    {
        "nom": "Audiovisuel",
        "email": "dsin-audiovisuel@univ-corse.fr",
        "description": "Équipements audiovisuels, visioconférence, projecteurs",
    },
    {
        "nom": "Copieurs",
        "email": "hotline xerox",
        "description": "Imprimantes, copieurs, photocopieuses Xerox",
    },
    {
        "nom": "Suivi de commande",
        "email": "brunet_f@univ-corse.fr",
        "description": "Suivi des commandes de matériel informatique",
    },
]


def init_techniciens():
    """Initialise la table des techniciens avec les données par défaut."""
    with Session(engine) as session:
        for tech_data in TECHNICIENS_DATA:
            existing = session.exec(
                select(Technicien).where(Technicien.nom == tech_data["nom"])
            ).first()
            if not existing:
                technicien = Technicien(**tech_data)
                session.add(technicien)
        session.commit()


def get_technicien_by_nom(nom: str) -> Technicien | None:
    """Récupère un technicien par son nom de catégorie."""
    with Session(engine) as session:
        return session.exec(
            select(Technicien).where(Technicien.nom == nom)
        ).first()


def get_all_categories() -> list[str]:
    """Retourne la liste de tous les noms de catégories disponibles."""
    return [t["nom"] for t in TECHNICIENS_DATA]
