import os
from sqlmodel import create_engine, SQLModel, text

# L'URL de la base de données depuis l'environnement ou SQLite par défaut
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db/mydatabase")

# Pour SQLite, on n'a pas besoin d'options spéciales
# Pour PostgreSQL en prod, on garde les options par défaut
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=True)

def create_db_and_tables():
    # Si PostgreSQL, créer l'extension vector
    if "postgresql" in DATABASE_URL:
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
        except Exception as e:
            print(f"Note: Extension vector non créée (normal si pas PostgreSQL): {e}")
    
    # Créer toutes les tables
    SQLModel.metadata.create_all(engine)