from openai import OpenAI

from app.config import OPENAI_API_KEY
from app.database import fetch_metric_definition
from app.services.query_engine import analyze_question, build_sql_from_analysis


def generate_sql_with_llm(question: str, metric_name: str | None = None) -> str:
    analysis = analyze_question(question)
    metric_name = metric_name or analysis.get("metric_name")
    metric = fetch_metric_definition(metric_name) if metric_name else None
    if not metric or metric["approval_status"] != "approved":
        raise ValueError(
            f"No approved business definition is available for {metric_name or 'this request'}."
        )

    if not OPENAI_API_KEY:
        return build_sql_from_analysis(analysis)

    client = OpenAI(api_key=OPENAI_API_KEY, timeout=20.0, max_retries=1)
    schema_hint = """
    Schema:
    customers(customer_id, customer_name, segment, signup_date, region)
    orders(order_id, customer_id, order_date, total_amount, status)
    order_items(order_item_id, order_id, product_id, quantity, unit_price, discount)
    products(product_id, product_name, category, unit_price)
    categories(category_id, category_name, region)
    """
    prompt = (
        "You are a SQL generation assistant for a read-only analytics dataset. "
        "Only return a single SQLite SELECT query and never write commands. "
        f"Question: {question}\nApproved metric: {metric['name']}\n"
        f"Approved definition: {metric['definition_sql']}\nSchema:\n{schema_hint}"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Generate accurate SQLite SELECT statements from business questions."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("The SQL generation provider returned an empty response.")
    return content.strip()
