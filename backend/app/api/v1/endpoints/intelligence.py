import json
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user, require_org_role
from app.db.session import get_db
from app.models.auth import User, Workspace
from app.models.intelligence import DatabaseConnection, DatabaseTable, QueryRequest
from app.schemas.intelligence import (
    AIRequest,
    AIResponse,
    ConnectionCreate,
    ConnectionRead,
    TableRead,
)
from app.schemas.query import (
    QueryApprovalRequest,
    QueryExecutionRead,
    QueryInterpretRequest,
    QueryRequestRead,
)
from app.services.connectors import (
    ensure_demo_database,
    extract_schema,
    test_connection,
    validate_external_url,
)
from app.services.credentials import decrypt_text, encrypt_text
from app.services.providers import get_llm_provider
from app.services.query_guard import sql_hash, validate_read_only_sql
from app.services.query_intelligence import build_query_plan

router = APIRouter(tags=["database-intelligence"])


def get_workspace(
    organization_id: str,
    workspace_id: str,
    user: User,
    session: Session,
) -> Workspace:
    require_org_role(organization_id, "viewer", user, session)
    workspace = session.get(Workspace, workspace_id)
    if workspace is None or workspace.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.get(
    "/organizations/{organization_id}/workspaces/{workspace_id}/connections",
    response_model=list[ConnectionRead],
)
def list_connections(
    organization_id: str,
    workspace_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[DatabaseConnection]:
    get_workspace(organization_id, workspace_id, user, session)
    return list(session.scalars(
        select(DatabaseConnection).where(
            DatabaseConnection.organization_id == organization_id,
            DatabaseConnection.workspace_id == workspace_id,
        )
    ).all())


@router.post(
    "/organizations/{organization_id}/workspaces/{workspace_id}/connections",
    response_model=ConnectionRead,
    status_code=201,
)
def create_connection(
    organization_id: str,
    workspace_id: str,
    request: ConnectionCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> DatabaseConnection:
    get_workspace(organization_id, workspace_id, user, session)
    require_org_role(organization_id, "admin", user, session)
    credentials_json = json.dumps(request.credentials, sort_keys=True)
    connection = DatabaseConnection(
        organization_id=organization_id,
        workspace_id=workspace_id,
        name=request.name,
        dialect=request.dialect,
        encrypted_credentials=encrypt_text(credentials_json),
        status="pending",
    )
    session.add(connection)
    session.commit()
    session.refresh(connection)
    return connection


def get_connection(
    organization_id: str,
    workspace_id: str,
    connection_id: str,
    user: User,
    session: Session,
) -> DatabaseConnection:
    get_workspace(organization_id, workspace_id, user, session)
    connection = session.get(DatabaseConnection, connection_id)
    if (
        connection is None
        or connection.organization_id != organization_id
        or connection.workspace_id != workspace_id
    ):
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection


def connection_url(connection: DatabaseConnection) -> str:
    credentials = json.loads(decrypt_text(connection.encrypted_credentials))
    if connection.dialect == "sqlite_demo":
        return ensure_demo_database()
    return validate_external_url(connection.dialect, credentials)


@router.post(
    "/organizations/{organization_id}/workspaces/{workspace_id}/connections/{connection_id}/test",
    response_model=ConnectionRead,
)
def test_connection_endpoint(
    organization_id: str,
    workspace_id: str,
    connection_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> DatabaseConnection:
    connection = get_connection(
        organization_id,
        workspace_id,
        connection_id,
        user,
        session,
    )
    try:
        test_connection(connection_url(connection))
        connection.status = "connected"
        connection.last_error = None
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        connection.status = "failed"
        connection.last_error = "Invalid or unreachable database connection"
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    connection.last_tested_at = datetime.now(UTC)
    session.commit()
    session.refresh(connection)
    return connection


@router.post(
    "/organizations/{organization_id}/workspaces/{workspace_id}/connections/{connection_id}/sync",
    response_model=list[TableRead],
)
def sync_connection(
    organization_id: str,
    workspace_id: str,
    connection_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[DatabaseTable]:
    connection = get_connection(
        organization_id,
        workspace_id,
        connection_id,
        user,
        session,
    )
    require_org_role(organization_id, "admin", user, session)
    try:
        url = connection_url(connection)
        test_connection(url)
        extracted = extract_schema(url)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        connection.status = "failed"
        connection.last_error = "Schema synchronization failed safely"
        session.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    for existing in list(connection.tables):
        session.delete(existing)
    session.flush()
    for table in extracted:
        session.add(DatabaseTable(
            connection_id=connection.id,
            schema_name=table.schema_name,
            table_name=table.table_name,
            columns=table.columns,
            foreign_keys=table.foreign_keys,
        ))
    connection.status = "connected"
    connection.last_error = None
    connection.last_tested_at = datetime.now(UTC)
    connection.last_synced_at = datetime.now(UTC)
    session.commit()
    session.refresh(connection)
    return list(connection.tables)


@router.get(
    "/organizations/{organization_id}/workspaces/{workspace_id}/connections/{connection_id}/schema",
    response_model=list[TableRead],
)
def get_schema(
    organization_id: str,
    workspace_id: str,
    connection_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[DatabaseTable]:
    connection = get_connection(
        organization_id,
        workspace_id,
        connection_id,
        user,
        session,
    )
    return list(session.scalars(
        select(DatabaseTable).where(DatabaseTable.connection_id == connection.id)
    ).all())


query_router = APIRouter(prefix="/queries", tags=["query-intelligence"])


def query_allowlists(
    connection: DatabaseConnection,
    session: Session,
) -> tuple[set[str], set[str]]:
    tables = list(session.scalars(
        select(DatabaseTable).where(DatabaseTable.connection_id == connection.id)
    ).all())
    table_names = {table.table_name.lower() for table in tables}
    column_names: set[str] = set()
    for table in tables:
        for column in table.columns:
            name = column.get("name")
            if isinstance(name, str):
                column_names.add(name.lower())
    return table_names, column_names


@query_router.post(
    "/organizations/{organization_id}/workspaces/{workspace_id}/connections/{connection_id}/interpret",
    response_model=QueryRequestRead,
)
def interpret_query(
    organization_id: str,
    workspace_id: str,
    connection_id: str,
    request: QueryInterpretRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> QueryRequest:
    connection = get_connection(
        organization_id,
        workspace_id,
        connection_id,
        user,
        session,
    )
    plan = build_query_plan(request.question)
    allowed_tables, allowed_columns = query_allowlists(connection, session)
    candidate_hash = None
    status_value = "clarification"
    generated_sql = plan.sql

    if plan.clarification is None and generated_sql:
        try:
            dialect = "sqlite" if connection.dialect == "sqlite_demo" else "postgres"
            validate_read_only_sql(
                generated_sql,
                allowed_tables,
                allowed_columns,
                dialect,
            )
            candidate_hash = sql_hash(generated_sql)
            status_value = "awaiting_approval"
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Generated SQL failed the safety policy: {exc}",
            ) from exc

    query_request = QueryRequest(
        organization_id=organization_id,
        workspace_id=workspace_id,
        connection_id=connection.id,
        created_by=user.id,
        question=request.question,
        intent=plan.intent,
        metric=plan.metric,
        generated_sql=generated_sql,
        explanation=plan.explanation,
        clarification=plan.clarification,
        candidate_hash=candidate_hash,
        status=status_value,
    )
    session.add(query_request)
    session.commit()
    session.refresh(query_request)
    return query_request


@query_router.post(
    "/organizations/{organization_id}/workspaces/{workspace_id}/requests/{request_id}/approve",
    response_model=QueryRequestRead,
)
def approve_query(
    organization_id: str,
    workspace_id: str,
    request_id: str,
    request: QueryApprovalRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> QueryRequest:
    get_workspace(organization_id, workspace_id, user, session)
    require_org_role(organization_id, "member", user, session)
    query_request = session.get(QueryRequest, request_id)
    if (
        query_request is None
        or query_request.organization_id != organization_id
        or query_request.workspace_id != workspace_id
        or query_request.status != "awaiting_approval"
    ):
        raise HTTPException(status_code=404, detail="Query request not found or already resolved")
    if sql_hash(request.sql) != query_request.candidate_hash:
        raise HTTPException(
            status_code=409,
            detail="Approved SQL no longer matches the generated SQL candidate",
        )
    if request.candidate_hash != query_request.candidate_hash:
        raise HTTPException(status_code=409, detail="Candidate hash mismatch")

    connection = session.get(DatabaseConnection, query_request.connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="Database connection not found")
    allowed_tables, allowed_columns = query_allowlists(connection, session)
    dialect = "sqlite" if connection.dialect == "sqlite_demo" else "postgres"
    try:
        validate_read_only_sql(
            request.sql,
            allowed_tables,
            allowed_columns,
            dialect,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Approved SQL failed the safety policy: {exc}",
        ) from exc

    query_request.approved_sql = request.sql
    query_request.status = "approved"
    session.commit()
    session.refresh(query_request)
    return query_request


@query_router.post(
    "/organizations/{organization_id}/workspaces/{workspace_id}/requests/{request_id}/execute",
    response_model=QueryExecutionRead,
)
def execute_query(
    organization_id: str,
    workspace_id: str,
    request_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> QueryExecutionRead:
    get_workspace(organization_id, workspace_id, user, session)
    require_org_role(organization_id, "member", user, session)
    query_request = session.get(QueryRequest, request_id)
    if (
        query_request is None
        or query_request.organization_id != organization_id
        or query_request.workspace_id != workspace_id
        or query_request.status != "approved"
        or not query_request.approved_sql
    ):
        raise HTTPException(status_code=409, detail="A safe approved query is required")

    connection = session.get(DatabaseConnection, query_request.connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="Database connection not found")
    allowed_tables, allowed_columns = query_allowlists(connection, session)
    dialect = "sqlite" if connection.dialect == "sqlite_demo" else "postgres"
    try:
        validate_read_only_sql(
            query_request.approved_sql,
            allowed_tables,
            allowed_columns,
            dialect,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Approved SQL failed revalidation: {exc}",
        ) from exc

    url = connection_url(connection)
    engine = create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5} if url.startswith("postgresql") else {},
    )
    try:
        with engine.begin() as connection_session:
            if url.startswith("postgresql"):
                connection_session.execute(text("SET LOCAL statement_timeout = '5s'"))
                connection_session.execute(text("SET TRANSACTION READ ONLY"))
            else:
                connection_session.execute(text("PRAGMA query_only = ON"))
            result = connection_session.execute(text(query_request.approved_sql))
            keys = list(result.keys())
            fetched = result.fetchmany(101)
            rows = [
                [
                    str(value) if hasattr(value, "isoformat") else value
                    for value in row
                ]
                for row in fetched[:100]
            ]
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Query execution failed safely",
        ) from exc
    finally:
        engine.dispose()

    return QueryExecutionRead(
        id=query_request.id,
        columns=keys,
        rows=rows,
        row_count=len(rows),
    )


ai_router = APIRouter(prefix="/ai", tags=["ai-provider"])


@ai_router.post("/generate", response_model=AIResponse)
def generate(
    request: AIRequest,
    user: Annotated[User, Depends(get_current_user)],
) -> AIResponse:
    del user
    try:
        result = get_llm_provider().generate(request.prompt, request.prompt_version)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return AIResponse(
        provider="gemini",
        model=result.model,
        prompt_version=request.prompt_version,
        answer=result.answer,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
