from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app import main
from app.main import app


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_database_health_returns_503_when_database_is_unavailable(monkeypatch):
    def raise_database_error():
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(main, "test_connection", raise_database_error)

    response = TestClient(app).get("/health/db")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
