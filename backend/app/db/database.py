
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

def normalize_database_url(url: str) -> str:
    """Hosted providers (Neon, Render, ...) give "postgresql://..." or "postgres://...".
    SQLAlchemy needs the driver named explicitly, so add it here."""
    url = url.strip()
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


DATABASE_URL = normalize_database_url(
    os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://marketpulse:password1@localhost:5432/marketpulse",
    )
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as db:
        yield db

def test_connection():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT 1")
        )
        return result.scalar()
