import uuid
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models.auth  # noqa: F401
import app.models.intelligence  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
TestSession = sessionmaker(bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def register_owner() -> tuple[dict[str, object], str, str]:
    suffix = uuid.uuid4().hex
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"intelligence-{suffix}@example.com",
            "password": "a-secure-password",
            "display_name": "Intelligence Owner",
            "organization_name": "Intelligence Tenant",
        },
    )
    assert response.status_code == 201
    tokens = response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    organizations = client.get("/api/v1/organizations", headers=headers)
    organization_id = organizations.json()[0]["id"]
    created = client.post(
        f"/api/v1/organizations/{organization_id}/workspaces",
        headers=headers,
        json={"name": "Analytics", "slug": "analytics"},
    )
    return tokens, organization_id, created.json()["id"]


def test_demo_connection_sync_and_relationship_metadata() -> None:
    tokens, organization_id, workspace_id = register_owner()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    base = f"/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/connections"

    created = client.post(
        base,
        headers=headers,
        json={
            "name": "Demo Analytics",
            "dialect": "sqlite_demo",
            "credentials": {},
        },
    )
    assert created.status_code == 201
    connection_id = created.json()["id"]

    tested = client.post(f"{base}/{connection_id}/test", headers=headers)
    assert tested.status_code == 200
    assert tested.json()["status"] == "connected"

    synced = client.post(f"{base}/{connection_id}/sync", headers=headers)
    assert synced.status_code == 200
    table_names = {table["table_name"] for table in synced.json()}
    assert {"customers", "orders"} <= table_names

    schema = client.get(f"{base}/{connection_id}/schema", headers=headers)
    assert schema.status_code == 200
    orders = next(table for table in schema.json() if table["table_name"] == "orders")
    assert orders["foreign_keys"][0]["referred_table"] == "customers"


def test_invalid_postgresql_connection_fails_safely() -> None:
    tokens, organization_id, workspace_id = register_owner()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    base = f"/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/connections"
    created = client.post(
        base,
        headers=headers,
        json={
            "name": "Invalid PostgreSQL",
            "dialect": "postgresql",
            "credentials": {
                "host": "127.0.0.1",
                "port": "invalid",
                "database": "missing",
                "username": "missing",
                "password": "missing",
            },
        },
    )
    assert created.status_code == 201
    tested = client.post(
        f"{base}/{created.json()['id']}/test",
        headers=headers,
    )
    assert tested.status_code == 422
    assert "password" not in tested.text.lower()


def test_ai_provider_without_credentials_fails_without_exposure() -> None:
    tokens, _, _ = register_owner()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = client.post(
        "/api/v1/ai/generate",
        headers=headers,
        json={"prompt": "Summarize this demo data", "prompt_version": "v1"},
    )
    assert response.status_code == 503
    assert "Gemini API key" in response.json()["detail"]
    assert "gemini_api_key" not in response.text
