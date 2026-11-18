import re
from typing import Any

from app.database import fetch_metric_definition


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().lower()


def analyze_question(question: str) -> dict[str, Any]:
    cleaned = clean_text(question)
    if not cleaned:
        raise ValueError("Please provide a business question to generate a query.")

    metric_name = None
    if "revenue" in cleaned:
        metric_name = "Total Revenue"
    elif "net profit" in cleaned:
        metric_name = "Net Profit"
    elif "gross profit" in cleaned or "profit" in cleaned:
        metric_name = "Gross Profit"
    elif "active customer" in cleaned or "customers" in cleaned:
        metric_name = "Active Customers"
    elif "average order" in cleaned or "aov" in cleaned:
        metric_name = "Average Order Value"

    if metric_name is None:
        metric_name = "Total Revenue"

    explicit_metric = any(
        token in cleaned
        for token in ["revenue", "profit", "units sold", "unit sales"]
    )
    ambiguous_product_request = any(
        token in cleaned
        for token in ["best-performing", "best performing", "top products", "best products"]
    )
    if ambiguous_product_request and not explicit_metric:
        return {
            "metric_name": metric_name,
            "ambiguous": True,
            "clarification": "Would you like to rank products by revenue, units sold, or profit?",
            "limit": 10,
            "sort": "DESC",
            "time_window": "last 6 months",
        }

    if "last six months" in cleaned or "last 6 months" in cleaned or "6 months" in cleaned:
        time_window = "last 6 months"
    elif "last month" in cleaned:
        time_window = "last month"
    elif "last year" in cleaned or "year" in cleaned:
        time_window = "last year"
    else:
        time_window = "all time"

    if "top " in cleaned or "highest" in cleaned or "best" in cleaned:
        sort = "DESC"
    else:
        sort = "DESC"

    return {
        "metric_name": metric_name,
        "ambiguous": False,
        "clarification": None,
        "limit": 10,
        "sort": sort,
        "time_window": time_window,
    }


def build_sql_from_analysis(analysis: dict[str, Any]) -> str:
    metric_name = analysis.get("metric_name", "Total Revenue")
    limit = analysis.get("limit", 10)
    time_window = analysis.get("time_window", "all time")
    date_filter = ""
    if time_window == "last month":
        date_filter = "o.order_date >= date('now', '-1 month')"
    elif time_window == "last 6 months":
        date_filter = "o.order_date >= date('now', '-6 months')"
    elif time_window == "last year":
        date_filter = "o.order_date >= date('now', '-1 year')"
    where_clause = "WHERE o.status = 'paid'"
    if date_filter:
        where_clause += f" AND {date_filter}"

    if metric_name == "Total Revenue":
        return (
            "SELECT p.product_name AS product_name, ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS total_revenue "
            "FROM order_items oi "
            "JOIN products p ON p.product_id = oi.product_id "
            "JOIN orders o ON o.order_id = oi.order_id "
            f"{where_clause} "
            "GROUP BY p.product_name "
            "ORDER BY total_revenue DESC "
            f"LIMIT {limit};"
        )

    if metric_name == "Gross Profit":
        return (
            "SELECT p.product_name AS product_name, ROUND(SUM((oi.quantity * oi.unit_price) - (oi.quantity * 85.0)), 2) AS gross_profit "
            "FROM order_items oi "
            "JOIN products p ON p.product_id = oi.product_id "
            "JOIN orders o ON o.order_id = oi.order_id "
            f"{where_clause} "
            "GROUP BY p.product_name "
            "ORDER BY gross_profit DESC "
            f"LIMIT {limit};"
        )

    if metric_name == "Net Profit":
        return (
            "SELECT p.product_name AS product_name, ROUND(SUM((oi.quantity * oi.unit_price) - (oi.quantity * 110.0)), 2) AS net_profit "
            "FROM order_items oi "
            "JOIN products p ON p.product_id = oi.product_id "
            "JOIN orders o ON o.order_id = oi.order_id "
            f"{where_clause} "
            "GROUP BY p.product_name "
            "ORDER BY net_profit DESC "
            f"LIMIT {limit};"
        )

    if metric_name == "Active Customers":
        return (
            "SELECT c.region AS region, COUNT(DISTINCT c.customer_id) AS active_customers "
            "FROM customers c "
            "JOIN orders o ON o.customer_id = c.customer_id "
            f"{where_clause} "
            "GROUP BY c.region "
            "ORDER BY active_customers DESC "
            f"LIMIT {limit};"
        )

    if metric_name == "Average Order Value":
        return (
            "SELECT c.segment AS segment, ROUND(AVG(o.total_amount), 2) AS average_order_value "
            "FROM orders o "
            "JOIN customers c ON c.customer_id = o.customer_id "
            f"{where_clause} "
            "GROUP BY c.segment "
            "ORDER BY average_order_value DESC "
            f"LIMIT {limit};"
        )

    return "SELECT 1;"


def generate_sql_for_question(question: str, dialect: str = "sqlite") -> dict[str, Any]:
    analysis = analyze_question(question)
    if analysis.get("ambiguous"):
        raise ValueError(analysis["clarification"])

    metric_details = {
        "name": analysis.get("metric_name"),
        "definition": "Approved metric retrieval from the semantic metric library.",
    }

    metric = fetch_metric_definition(analysis.get("metric_name"))
    if not metric or metric["approval_status"] != "approved":
        raise ValueError(
            f"No approved business definition is available for {analysis.get('metric_name')}."
        )
    metric_details = metric

    sql = build_sql_from_analysis(analysis)
    return {
        "status": "ready",
        "question": question,
        "dialect": dialect,
        "metric": metric_details,
        "sql": sql,
        "analysis": analysis,
    }
