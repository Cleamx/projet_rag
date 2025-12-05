import os

from sqlmodel import SQLModel, create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@db/mydatabase"
)

connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=True)


def create_db_and_tables():
    if "postgresql" in DATABASE_URL:
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("CREATE EXTENSION IF NOT EXISTS vector")
                )
                conn.commit()
        except Exception as e:
            print(
                f"Note: Extension vector non créée: {e}"
            )

    SQLModel.metadata.create_all(engine)
