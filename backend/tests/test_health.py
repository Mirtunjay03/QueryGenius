from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_db
from app.main import app

engine = create_engine("sqlite://")
TestSession = sessionmaker(bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_liveness_returns_ok() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_checks_database() -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_versioned_readiness_route() -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
