from app.services.query_guard import validate_read_only_sql
from app.services.query_intelligence import build_query_plan


def test_approved_select_is_validated_with_allowlists() -> None:
    expression = validate_read_only_sql(
        "SELECT COUNT(*) AS customer_count FROM customers LIMIT 1",
        {"customers", "orders"},
        {"id", "name", "email", "country", "customer_id", "status", "amount", "created_at"},
        "sqlite",
    )
    assert expression is not None


def test_destructive_queries_are_rejected() -> None:
    for sql in (
        "DELETE FROM customers",
        "DROP TABLE customers",
        "UPDATE customers SET name = 'changed'",
        "INSERT INTO customers (name) VALUES ('test')",
    ):
        try:
            validate_read_only_sql(
                sql,
                {"customers"},
                {"id", "name"},
                "sqlite",
            )
        except ValueError:
            continue
        raise AssertionError(f"Unsafe SQL was accepted: {sql}")


def test_allowlist_and_limit_are_enforced() -> None:
    try:
        validate_read_only_sql(
            "SELECT * FROM secrets LIMIT 10",
            {"customers"},
            {"id", "name"},
            "sqlite",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Out-of-allowlist table was accepted")

    try:
        validate_read_only_sql(
            "SELECT id FROM customers",
            {"customers"},
            {"id"},
            "sqlite",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("SELECT without LIMIT was accepted")


def test_demo_questions_generate_grounded_sql() -> None:
    count = build_query_plan("How many customers are there?")
    assert count.metric == "customer_count"
    assert count.sql == "SELECT COUNT(*) AS customer_count\nFROM customers\nLIMIT 1"

    revenue = build_query_plan("What is our paid revenue?")
    assert revenue.metric == "paid_revenue"
    assert "WHERE o.status" not in (revenue.sql or "")
    assert "FROM orders" in (revenue.sql or "")
    assert "WHERE status = 'paid'" in (revenue.sql or "")

    ambiguous = build_query_plan("Show me some data")
    assert ambiguous.sql is None
    assert ambiguous.clarification is not None
