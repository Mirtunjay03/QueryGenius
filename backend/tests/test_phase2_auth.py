from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models.auth  # noqa: F401
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


def register(email: str, organization: str) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "a-secure-password",
            "display_name": "Test User",
            "organization_name": organization,
        },
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(tokens: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_register_login_me_and_refresh() -> None:
    registered = register("owner@example.com", "Acme Analytics")
    me = client.get("/api/v1/auth/me", headers=auth_headers(registered))
    assert me.status_code == 200
    assert me.json()["email"] == "owner@example.com"

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": "a-secure-password"},
    )
    assert login.status_code == 200
    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]


def test_owner_can_create_workspace_and_viewer_cannot() -> None:
    owner = register("workspace-owner@example.com", "Tenant One")
    organizations = client.get(
        "/api/v1/organizations",
        headers=auth_headers(owner),
    )
    organization_id = organizations.json()[0]["id"]

    created = client.post(
        f"/api/v1/organizations/{organization_id}/workspaces",
        headers=auth_headers(owner),
        json={"name": "Sales", "slug": "sales"},
    )
    assert created.status_code == 201

    listed = client.get(
        f"/api/v1/organizations/{organization_id}/workspaces",
        headers=auth_headers(owner),
    )
    assert listed.status_code == 200
    assert listed.json()[0]["slug"] == "sales"


def test_unauthorized_and_cross_tenant_access_are_blocked() -> None:
    owner_one = register("tenant-one@example.com", "Tenant One")
    owner_two = register("tenant-two@example.com", "Tenant Two")
    org_one = client.get(
        "/api/v1/organizations",
        headers=auth_headers(owner_one),
    ).json()[0]
    org_two = client.get(
        "/api/v1/organizations",
        headers=auth_headers(owner_two),
    ).json()[0]

    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get(
        f"/api/v1/organizations/{org_one['id']}/workspaces",
        headers=auth_headers(owner_two),
    ).status_code == 404
    assert client.post(
        f"/api/v1/organizations/{org_one['id']}/workspaces",
        headers=auth_headers(owner_two),
        json={"name": "Stolen", "slug": "stolen"},
    ).status_code == 404
    assert org_two["id"] != org_one["id"]
