import sqlite3

import pytest
from app import create_app
from app.database import fetch_query_history, initialize_database
from app.extensions import db
from app.models import User
from app.routes import _execute_query
from app.services.query_engine import analyze_question, generate_sql_for_question
from app.services.security import validate_sql_statement


@pytest.fixture()
def client(tmp_path):
    database_path = str(tmp_path / "accounts.sqlite3").replace("\\", "/")
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
        }
    )
    with app.test_client() as client:
        yield client


def _login(client):
    return client.post(
        "/login",
        data={"email": "tester@example.com", "password": "test-password-long"},
        follow_redirects=True,
    )


@pytest.fixture(autouse=True)
def create_test_user(client):
    with client.application.app_context():
        existing = db.session.execute(
            db.select(User).filter_by(email="tester@example.com")
        ).scalar_one_or_none()
        if not existing:
            user = User(email="tester@example.com")
            user.set_password("test-password-long")
            db.session.add(user)
            db.session.commit()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_dashboard_and_query_require_authentication(client):
    assert client.get("/").status_code == 302
    response = client.post("/api/query", json={"question": "show revenue"})
    assert response.status_code == 401


def test_login_rejects_bad_password_and_accepts_valid_credentials(client):
    bad_response = client.post(
        "/login",
        data={"email": "tester@example.com", "password": "wrong-password"},
    )
    assert bad_response.status_code == 200
    assert b"Email or password is incorrect" in bad_response.data

    assert _login(client).status_code == 200
    assert client.get("/").status_code == 200


def test_login_form_enforces_csrf(tmp_path):
    database_path = str(tmp_path / "csrf-accounts.sqlite3").replace("\\", "/")
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
        }
    )

    response = app.test_client().post(
        "/login",
        data={"email": "tester@example.com", "password": "test-password-long"},
    )

    assert response.status_code == 400


def test_query_generation_and_validation():
    result = generate_sql_for_question("Show me the top 10 products by total revenue in the last six months.")
    assert result["status"] == "ready"
    assert "SELECT" in result["sql"].upper()
    assert "1 - oi.discount" in result["sql"]
    assert "o.status = 'paid'" in result["sql"]

    security = validate_sql_statement(result["sql"])
    assert security["approved"] is True
    assert "LIMIT" in security["normalized_sql"].upper()


def test_ambiguous_question_is_rejected():
    question = "Show me the best-performing products."
    with pytest.raises(ValueError):
        generate_sql_for_question(question)

    analysis = analyze_question(question)
    assert analysis["ambiguous"] is True


def test_unapproved_metric_cannot_be_queried():
    with pytest.raises(ValueError, match="No approved business definition"):
        generate_sql_for_question("Show me gross profit by product.")


def test_rejects_write_sql():
    with pytest.raises(ValueError):
        validate_sql_statement("DELETE FROM orders;")


def test_query_guard_caps_limits_and_preserves_smaller_limit():
    small_limit = validate_sql_statement("SELECT order_id FROM orders LIMIT 5")
    large_limit = validate_sql_statement("SELECT order_id FROM orders LIMIT 50000")

    assert "LIMIT 5" in small_limit["normalized_sql"]
    assert "LIMIT 1000" in large_limit["normalized_sql"]


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM other_schema.orders",
        "SELECT * FROM sqlite_master",
        "SELECT * FROM orders OFFSET 10000",
        "SELECT * FROM orders; DELETE FROM orders",
        "SELECT load_extension('extension') FROM orders",
        "SELECT * FROM orders",
        "SELECT private_column FROM orders",
    ],
)
def test_query_guard_rejects_unsafe_selects(sql):
    with pytest.raises(ValueError):
        validate_sql_statement(sql)


def test_query_guard_allows_read_only_cte():
    sql = (
        "WITH revenue AS ("
        "SELECT product_id, SUM(quantity * unit_price) AS amount "
        "FROM order_items GROUP BY product_id"
        ") SELECT p.product_name, revenue.amount FROM revenue "
        "JOIN products p ON p.product_id = revenue.product_id LIMIT 10"
    )

    assert validate_sql_statement(sql)["approved"] is True



def test_query_endpoint_returns_rows(client):
    _login(client)
    response = client.post(
        "/api/query",
        json={"question": "Show me the top products by total revenue in the last six months."},
    )

    assert response.status_code == 200
    assert response.get_json()["rows"]
    with client.application.app_context():
        user_id = db.session.execute(
            db.select(User).filter_by(email="tester@example.com")
        ).scalar_one().id
        latest_question = fetch_query_history(limit=1, user_id=user_id)[0]["question"]
        assert fetch_query_history(limit=1, user_id=user_id + 10000) == []

        initialize_database()

        assert fetch_query_history(limit=1, user_id=user_id)[0]["question"] == latest_question


def test_query_execution_connection_is_read_only():
    with pytest.raises(sqlite3.OperationalError):
        _execute_query("DELETE FROM orders", max_rows=1, timeout_seconds=1)


def test_query_execution_enforces_timeout():
    sql = (
        "WITH RECURSIVE sequence(value) AS ("
        "SELECT 1 UNION ALL SELECT value + 1 FROM sequence WHERE value < 100000000"
        ") SELECT MAX(value) FROM sequence"
    )

    with pytest.raises(sqlite3.OperationalError, match="interrupted"):
        _execute_query(sql, max_rows=1, timeout_seconds=1)
