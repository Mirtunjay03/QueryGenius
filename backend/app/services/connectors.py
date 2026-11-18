from dataclasses import dataclass

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError


@dataclass(frozen=True)
class SchemaTable:
    schema_name: str
    table_name: str
    columns: list[dict[str, object]]
    foreign_keys: list[dict[str, object]]


def validate_external_url(dialect: str, credentials: dict[str, str]) -> str:
    if dialect == "postgresql":
        host = credentials.get("host", "").strip()
        database = credentials.get("database", "").strip()
        username = credentials.get("username", "").strip()
        password = credentials.get("password", "")
        port = credentials.get("port", "5432").strip()
        sslmode = credentials.get("sslmode", "require").strip()
        if not all([host, database, username, password]):
            raise ValueError("PostgreSQL host, database, username, and password are required")
        if any(mark in host for mark in ("@", "/", "?", "#")):
            raise ValueError("Invalid PostgreSQL host")
        if not port.isdigit():
            raise ValueError("Invalid PostgreSQL port")
        url = URL.create(
            "postgresql+psycopg",
            username=username,
            password=password,
            host=host,
            port=int(port),
            database=database,
            query={"sslmode": sslmode},
        )
        return url.render_as_string(hide_password=False)
    if dialect == "sqlite_demo":
        return "sqlite:///./querygenius-demo.db"
    raise ValueError("Unsupported database dialect")


def ensure_demo_database() -> str:
    url = "sqlite:///./querygenius-demo.db"
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                country TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        ))
        connection.execute(text(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
            """
        ))
        connection.execute(text(
            "DELETE FROM orders"
        ))
        connection.execute(text(
            "DELETE FROM customers"
        ))
        connection.execute(text(
            """
            INSERT INTO customers (id, name, email, country, created_at) VALUES
            (1, 'Asha Sharma', 'asha@example.com', 'India', '2026-01-10'),
            (2, 'Marco Silva', 'marco@example.com', 'Brazil', '2026-01-12'),
            (3, 'Emma Chen', 'emma@example.com', 'Singapore', '2026-01-15')
            """
        ))
        connection.execute(text(
            """
            INSERT INTO orders (id, customer_id, status, amount, created_at) VALUES
            (101, 1, 'paid', 129.90, '2026-01-11'),
            (102, 1, 'paid', 89.50, '2026-01-18'),
            (103, 2, 'pending', 249.00, '2026-01-20'),
            (104, 3, 'paid', 74.25, '2026-01-22')
            """
        ))
    return url


def test_connection(url: str) -> None:
    connect_args = {"connect_timeout": 5} if url.startswith("postgresql") else {}
    engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise ValueError("Connection test failed safely") from exc
    finally:
        engine.dispose()


def extract_schema(url: str) -> list[SchemaTable]:
    engine = create_engine(url, pool_pre_ping=True)
    inspector = inspect(engine)
    tables: list[SchemaTable] = []
    try:
        for schema in inspector.get_schema_names():
            if schema in {"information_schema", "pg_catalog"}:
                continue
            for table_name in inspector.get_table_names(schema=schema):
                columns = []
                for column in inspector.get_columns(table_name, schema=schema):
                    columns.append({
                        "name": str(column["name"]),
                        "type": str(column["type"]),
                        "nullable": bool(column.get("nullable", True)),
                        "primary_key": bool(column.get("primary_key", False)),
                        "default": (
                            None
                            if column.get("default") is None
                            else str(column["default"])
                        ),
                    })
                foreign_keys: list[dict[str, object]] = [
                    {
                        "name": foreign_key.get("name"),
                        "constrained_columns": foreign_key.get("constrained_columns", []),
                        "referred_schema": foreign_key.get("referred_schema"),
                        "referred_table": foreign_key.get("referred_table"),
                        "referred_columns": foreign_key.get("referred_columns", []),
                    }
                    for foreign_key in inspector.get_foreign_keys(table_name, schema=schema)
                ]
                tables.append(SchemaTable(schema, table_name, columns, foreign_keys))
    finally:
        engine.dispose()
    return tables
