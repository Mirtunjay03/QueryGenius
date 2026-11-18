import hashlib
import re

import sqlglot
from sqlglot import exp

FORBIDDEN_EXPRESSIONS = tuple(
    getattr(exp, name)
    for name in (
        "Insert",
        "Update",
        "Delete",
        "Drop",
        "Alter",
        "Create",
        "Truncate",
        "Merge",
        "Command",
        "Copy",
    )
    if hasattr(exp, name)
)

def sql_hash(sql: str) -> str:
    canonical = re.sub(r"\s+", " ", sql.strip())
    return hashlib.sha256(canonical.encode()).hexdigest()


def validate_read_only_sql(
    sql: str,
    allowed_tables: set[str],
    allowed_columns: set[str] | None = None,
    dialect: str = "sqlite",
) -> exp.Expression:
    if not sql or len(sql) > 10_000:
        raise ValueError("SQL is empty or too large")

    try:
        statements = sqlglot.parse(sql, read=dialect)
    except sqlglot.errors.SqlglotError as exc:
        raise ValueError("SQL could not be parsed") from exc

    if len(statements) != 1 or statements[0] is None:
        raise ValueError("Exactly one SQL statement is required")
    expression = statements[0]

    if not isinstance(expression, exp.Select):
        raise ValueError("Only SELECT queries are allowed")
    if expression.find(*FORBIDDEN_EXPRESSIONS):
        raise ValueError("Destructive SQL expressions are forbidden")

    tables = {table.name.lower() for table in expression.find_all(exp.Table)}
    if not tables:
        raise ValueError("SQL must reference an allowlisted table")
    unknown_tables = tables - {table.lower() for table in allowed_tables}
    if unknown_tables:
        raise ValueError("SQL references a table outside the allowlist")

    if allowed_columns is not None:
        for column in expression.find_all(exp.Column):
            if column.name and column.name.lower() not in allowed_columns:
                raise ValueError("SQL references a column outside the allowlist")

    limit = expression.args.get("limit")
    if limit is None:
        raise ValueError("SELECT queries must include LIMIT")
    try:
        limit_value = int(limit.expression.name)
    except (TypeError, ValueError) as exc:
        raise ValueError("LIMIT must be a literal integer") from exc
    if limit_value < 1 or limit_value > 100:
        raise ValueError("LIMIT must be between 1 and 100")

    fetch_type = getattr(exp, "Fetch", None)
    if fetch_type is not None and expression.find(fetch_type):
        raise ValueError("FETCH is not allowed")
    return expression
