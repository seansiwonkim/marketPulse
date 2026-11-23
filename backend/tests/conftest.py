import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.articles import router as articles_router
from app.api.routes.status import router as status_router
from app.db.database import Base, get_db
from app.models.pipeline_run import PipelineRun  # noqa: F401  (registers the table)


@pytest.fixture
def db():
    # In-memory SQLite: fast, throwaway, never touches your Postgres data.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with sessionmaker(engine)() as session:
        yield session


@pytest.fixture
def client(db):
    app = FastAPI()
    app.include_router(articles_router)
    app.include_router(status_router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)
