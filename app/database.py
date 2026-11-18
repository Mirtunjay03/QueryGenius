import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import DB_PATH, DATA_DIR


def _connect(db_path: str = DB_PATH):
    os.makedirs(DATA_DIR, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS metric_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                definition_sql TEXT NOT NULL,
                source_tables TEXT NOT NULL,
                required_columns TEXT NOT NULL,
                default_aggregation TEXT NOT NULL,
                applicable_filters TEXT NOT NULL,
                owner TEXT NOT NULL,
                version TEXT NOT NULL,
                approval_status TEXT NOT NULL DEFAULT 'approved'
            );
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                generated_sql TEXT NOT NULL,
                dialect TEXT NOT NULL,
                metric_name TEXT,
                tables_used TEXT,
                explanation TEXT,
                approved INTEGER NOT NULL DEFAULT 0,
                user_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        history_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(query_history)")
        }
        if "user_id" not in history_columns:
            connection.execute("ALTER TABLE query_history ADD COLUMN user_id INTEGER")

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                customer_name TEXT NOT NULL,
                segment TEXT NOT NULL,
                signup_date TEXT NOT NULL,
                region TEXT NOT NULL
            );
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit_price REAL NOT NULL
            );
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
            );
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                order_item_id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                discount REAL NOT NULL DEFAULT 0,
                FOREIGN KEY(order_id) REFERENCES orders(order_id),
                FOREIGN KEY(product_id) REFERENCES products(product_id)
            );
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY,
                category_name TEXT NOT NULL,
                region TEXT NOT NULL
            );
            """
        )

        connection.execute("BEGIN IMMEDIATE")
        if connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
            seed_demo_data(connection)
        seed_metric_definitions(connection)
        connection.commit()


def seed_demo_data(connection: sqlite3.Connection):
    today = datetime.now(timezone.utc).date()
    customers = [
        (1, "Alice Johnson", "Enterprise", (today - timedelta(days=160)).isoformat(), "North"),
        (2, "Brian Chen", "SMB", (today - timedelta(days=110)).isoformat(), "West"),
        (3, "Carla Gomez", "Consumer", (today - timedelta(days=90)).isoformat(), "South"),
        (4, "David Reed", "Enterprise", (today - timedelta(days=50)).isoformat(), "East"),
        (5, "Eva Martin", "SMB", (today - timedelta(days=30)).isoformat(), "North"),
    ]
    products = [
        (1, "Analytics Pro", "Software", 299.00),
        (2, "Cloud Sync", "Software", 149.00),
        (3, "Smart Monitor", "Hardware", 420.00),
        (4, "Telemetry Hub", "Hardware", 890.00),
        (5, "Ops Dashboard", "Services", 1200.00),
    ]
    orders = [
        (101, 1, (today - timedelta(days=180)).isoformat(), 580.00, "paid"),
        (102, 2, (today - timedelta(days=150)).isoformat(), 299.00, "paid"),
        (103, 3, (today - timedelta(days=120)).isoformat(), 840.00, "paid"),
        (104, 4, (today - timedelta(days=90)).isoformat(), 1240.00, "paid"),
        (105, 1, (today - timedelta(days=45)).isoformat(), 420.00, "paid"),
        (106, 5, (today - timedelta(days=35)).isoformat(), 1490.00, "paid"),
        (107, 2, (today - timedelta(days=20)).isoformat(), 890.00, "paid"),
        (108, 3, (today - timedelta(days=10)).isoformat(), 760.00, "paid"),
        (109, 4, today.isoformat(), 530.00, "paid"),
    ]
    order_items = [
        (1, 101, 1, 2, 299.00, 0.0),
        (2, 102, 2, 1, 149.00, 0.0),
        (3, 103, 3, 2, 420.00, 0.0),
        (4, 104, 5, 1, 1200.00, 0.05),
        (5, 105, 3, 1, 420.00, 0.0),
        (6, 106, 4, 1, 890.00, 0.1),
        (7, 106, 2, 1, 149.00, 0.0),
        (8, 107, 4, 1, 890.00, 0.0),
        (9, 108, 1, 2, 299.00, 0.03),
        (10, 109, 5, 1, 530.00, 0.0),
    ]
    categories = [
        (1, "Software", "North"),
        (2, "Hardware", "West"),
        (3, "Services", "East"),
    ]

    connection.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers)
    connection.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)
    connection.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)
    connection.executemany(
        "INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)",
        order_items,
    )
    connection.executemany("INSERT INTO categories VALUES (?, ?, ?)", categories)


def seed_metric_definitions(connection: sqlite3.Connection):
    metrics = [
        (
            "Total Revenue",
            "Revenue from all paid order items after discounts.",
            "SUM(order_items.quantity * order_items.unit_price) - SUM(order_items.quantity * order_items.unit_price * order_items.discount)",
            "orders, order_items",
            "orders.order_id, order_items.quantity, order_items.unit_price, order_items.discount",
            "sum",
            "date, region, product, customer segment",
            "Finance Team",
            "v1",
            "approved",
        ),
        (
            "Gross Profit",
            "Difference between revenue and the cost of goods sold, represented here as a simplified margin model.",
            "SUM((order_items.quantity * order_items.unit_price) - (order_items.quantity * 85.0))",
            "order_items",
            "order_items.quantity, order_items.unit_price",
            "sum",
            "date, product, category",
            "Finance Team",
            "v1",
            "unapproved",
        ),
        (
            "Active Customers",
            "Count of unique customers with at least one paid order in the selected window.",
            "COUNT(DISTINCT customers.customer_id)",
            "customers, orders",
            "customers.customer_id, orders.order_date",
            "count",
            "date, region",
            "RevOps",
            "v1",
            "approved",
        ),
        (
            "Average Order Value",
            "Average total order value across paid orders.",
            "AVG(orders.total_amount)",
            "orders",
            "orders.total_amount, orders.order_date",
            "avg",
            "date, segment",
            "RevOps",
            "v1",
            "approved",
        ),
        (
            "Net Profit",
            "Simplified net profit estimate using revenue minus a fixed operational cost model.",
            "SUM((order_items.quantity * order_items.unit_price) - (order_items.quantity * 110.0))",
            "orders, order_items",
            "order_items.quantity, order_items.unit_price, orders.order_date",
            "sum",
            "date, product",
            "Finance Team",
            "v1",
            "unapproved",
        ),
    ]

    connection.executemany(
        """
        INSERT OR IGNORE INTO metric_definitions (
            name, description, definition_sql, source_tables, required_columns,
            default_aggregation, applicable_filters, owner, version, approval_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        metrics,
    )

    connection.execute(
        """
        UPDATE metric_definitions
        SET approval_status = 'unapproved'
        WHERE name = 'Gross Profit'
          AND definition_sql = 'SUM((order_items.quantity * order_items.unit_price) - (order_items.quantity * 85.0))'
        """
    )
    connection.execute(
        """
        UPDATE metric_definitions
        SET approval_status = 'unapproved'
        WHERE name = 'Net Profit'
          AND definition_sql = 'SUM((order_items.quantity * order_items.unit_price) - (order_items.quantity * 110.0))'
        """
    )


def fetch_metric_definitions():
    with _connect() as connection:
        rows = connection.execute(
            "SELECT name, description, definition_sql, source_tables, required_columns, default_aggregation, applicable_filters, owner, version, approval_status FROM metric_definitions ORDER BY name"
        ).fetchall()
        return [dict(row) for row in rows]


def fetch_metric_definition(name: str):
    with _connect() as connection:
        row = connection.execute(
            "SELECT name, description, definition_sql, source_tables, required_columns, default_aggregation, applicable_filters, owner, version, approval_status FROM metric_definitions WHERE name = ?",
            (name,),
        ).fetchone()
        return dict(row) if row else None


def fetch_query_history(limit: int = 10, user_id: int | None = None):
    from app.extensions import db
    from app.models import QueryHistory

    query = db.select(QueryHistory).order_by(QueryHistory.id.desc()).limit(limit)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    rows = db.session.execute(query).scalars()
    return [
        {
            "id": row.id,
            "question": row.question,
            "generated_sql": row.generated_sql,
            "dialect": row.dialect,
            "metric_name": row.metric_name,
            "tables_used": row.tables_used,
            "explanation": row.explanation,
            "approved": row.approved,
            "created_at": row.created_at.isoformat(sep=" ") if row.created_at else None,
        }
        for row in rows
    ]


def insert_query_history(
    question: str,
    generated_sql: str,
    dialect: str,
    metric_name: str | None,
    tables_used: str,
    explanation: str,
    user_id: int,
    approved: bool = True,
):
    from app.extensions import db
    from app.models import QueryHistory

    db.session.add(
        QueryHistory(
            question=question,
            generated_sql=generated_sql,
            dialect=dialect,
            metric_name=metric_name,
            tables_used=tables_used,
            explanation=explanation,
            approved=approved,
            user_id=user_id,
        )
    )
    db.session.commit()
