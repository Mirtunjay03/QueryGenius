import re
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.models.auth import Membership, MembershipRole, Organization, RefreshToken, User, Workspace
from app.schemas.auth import (
    LoginRequest,
    OrganizationRead,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
    WorkspaceCreate,
    WorkspaceRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "organization"


def issue_tokens(session: Session, user: User) -> TokenResponse:
    settings = get_settings()
    refresh = create_refresh_token()
    expires = datetime.now(UTC) + timedelta(days=settings.refresh_token_days)
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh),
            expires_at=expires,
        )
    )
    session.commit()
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=refresh,
        expires_in=settings.access_token_minutes * 60,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    session: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    if session.scalar(select(User).where(User.email == str(request.email).lower())):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    base_slug = slugify(request.organization_name)
    slug = base_slug
    counter = 2
    while session.scalar(select(Organization).where(Organization.slug == slug)):
        slug = f"{base_slug}-{counter}"
        counter += 1

    user = User(
        email=str(request.email).lower(),
        password_hash=hash_password(request.password),
        display_name=request.display_name,
    )
    organization = Organization(name=request.organization_name, slug=slug)
    session.add_all([user, organization])
    session.flush()
    session.add(
        Membership(
            organization_id=organization.id,
            user_id=user.id,
            role=MembershipRole.owner,
        )
    )
    session.commit()
    session.refresh(user)
    return issue_tokens(session, user)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, session: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    user = session.scalar(select(User).where(User.email == str(request.email).lower()))
    if (
        user is None
        or not verify_password(request.password, user.password_hash)
        or not user.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return issue_tokens(session, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest, session: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    token_hash = hash_refresh_token(request.refresh_token)
    record = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    now = datetime.now(UTC)
    if record is None or record.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid",
        )
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    record.revoked_at = now
    session.commit()
    user = session.get(User, record.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive")
    return issue_tokens(session, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: RefreshRequest, session: Annotated[Session, Depends(get_db)]) -> None:
    record = session.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(request.refresh_token)
        )
    )
    if record is not None and record.revoked_at is None:
        record.revoked_at = datetime.now(UTC)
        session.commit()


@router.get("/me", response_model=UserRead)
def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


organizations = APIRouter(prefix="/organizations", tags=["organizations"])


@organizations.get("", response_model=list[OrganizationRead])
def list_organizations(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[OrganizationRead]:
    rows = session.scalars(
        select(Membership).join(Organization).where(Membership.user_id == user.id)
    ).all()
    return [
        OrganizationRead(
            id=row.organization.id,
            name=row.organization.name,
            slug=row.organization.slug,
            role=row.role,
        )
        for row in rows
    ]


@organizations.get("/{organization_id}/workspaces", response_model=list[WorkspaceRead])
def list_workspaces(
    organization_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[Workspace]:
    from app.api.v1.dependencies import require_org_role

    require_org_role(organization_id, "viewer", user, session)
    workspaces = session.scalars(
        select(Workspace).where(Workspace.organization_id == organization_id)
    ).all()
    return list(workspaces)


@organizations.post(
    "/{organization_id}/workspaces",
    response_model=WorkspaceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace(
    organization_id: str,
    request: WorkspaceCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> Workspace:
    from app.api.v1.dependencies import require_org_role

    require_org_role(organization_id, "admin", user, session)
    if session.scalar(
        select(Workspace).where(
            Workspace.organization_id == organization_id,
            Workspace.slug == request.slug,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workspace slug already exists",
        )
    workspace = Workspace(organization_id=organization_id, name=request.name, slug=request.slug)
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace
