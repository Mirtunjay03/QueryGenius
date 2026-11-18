import re
from dataclasses import dataclass


@dataclass(frozen=True)
class QueryPlan:
    intent: str
    metric: str | None
    sql: str | None
    explanation: str
    clarification: str | None = None


def build_query_plan(question: str) -> QueryPlan:
    text = question.lower().strip()
    if not text:
        return QueryPlan(
            "unknown",
            None,
            None,
            "No question was provided.",
            "Please enter a business question.",
        )

    if re.search(r"\b(ambiguous|unclear|maybe|something|some data)\b", text):
        return QueryPlan(
            "clarification",
            None,
            None,
            "The request does not identify a specific metric or business entity.",
            "Should I count customers, calculate order revenue, or list recent orders?",
        )

    if re.search(r"\b(paid revenue|revenue|sales|amount)\b", text):
        if re.search(r"\b(customer|country|region)\b", text):
            return QueryPlan(
                "paid_revenue_by_customer",
                "paid_revenue",
                """
SELECT c.country AS country,
       COUNT(o.id) AS paid_orders,
       ROUND(SUM(o.amount), 2) AS revenue
FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE o.status = 'paid'
GROUP BY c.country
ORDER BY revenue DESC
LIMIT 100
""".strip(),
                "Sum of paid order amounts grouped by customer country.",
            )
        return QueryPlan(
            "paid_revenue",
            "paid_revenue",
            """
SELECT ROUND(SUM(amount), 2) AS revenue
FROM orders
WHERE status = 'paid'
LIMIT 1
""".strip(),
            "Sum the amount of rows whose status is paid.",
        )

    if re.search(r"\b(how many|count|number)\b", text) and re.search(r"\bcustomer", text):
        return QueryPlan(
            "customer_count",
            "customer_count",
            "SELECT COUNT(*) AS customer_count\nFROM customers\nLIMIT 1",
            "Count rows in the customers table.",
        )

    if re.search(r"\b(how many|count|number)\b", text) and re.search(r"\border", text):
        return QueryPlan(
            "order_count",
            "order_count",
            "SELECT COUNT(*) AS order_count\nFROM orders\nLIMIT 1",
            "Count rows in the orders table.",
        )

    if re.search(r"\b(list|show|top)\b", text) and re.search(r"\bcustomer", text):
        return QueryPlan(
            "customer_list",
            None,
            """
SELECT id, name, email, country
FROM customers
ORDER BY id
LIMIT 100
""".strip(),
            "List customer identity and country fields, capped at 100 rows.",
        )

    if re.search(r"\b(list|show|recent|top)\b", text) and re.search(r"\border", text):
        return QueryPlan(
            "order_list",
            None,
            """
SELECT id, customer_id, status, amount, created_at
FROM orders
ORDER BY created_at DESC
LIMIT 100
""".strip(),
            "List recent orders with status and amount, capped at 100 rows.",
        )

    return QueryPlan(
        "clarification",
        None,
        None,
        "The request is not specific enough to map it safely to the demo schema.",
        (
            "Which metric or entity do you mean: customer count, orders, "
            "paid revenue, or a customer/order list?"
        ),
    )
