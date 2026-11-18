from typing import Any

import sqlglot
from sqlglot import expressions as exp

from app.config import (
    ALLOWED_COLUMNS,
    ALLOWED_SCHEMAS,
    ALLOWED_TABLES,
    MAX_ROWS,
    QUERY_TIMEOUT_SECONDS,
)


def _inspect_statement(sql: str) -> Any:
    try:
        expressions = sqlglot.parse(sql, read="sqlite")
    except sqlglot.errors.ParseError as exc:
        raise ValueError("QueryGuard could not parse the generated SQL.") from exc
    if not expressions:
        raise ValueError("No SQL statement was parsed.")
    if len(expressions) != 1:
        raise ValueError("Only a single SQL statement is permitted.")
    return expressions[0]


def validate_sql_statement(sql: str) -> dict[str, Any]:
    if not sql or not sql.strip():
        raise ValueError("The generated SQL is empty.")

    statement = _inspect_statement(sql)
    expression_type = type(statement).__name__.upper()
    if expression_type != "SELECT":
        raise ValueError(f"QueryGuard rejected {expression_type}: only read-only SELECT statements are allowed.")
    if statement.find(exp.DML):
        raise ValueError("QueryGuard rejected a write operation inside the query.")

    if statement.find(exp.Into) or statement.find(exp.Lock) or statement.args.get("offset"):
        raise ValueError("QueryGuard rejected SELECT statements with write or locking clauses.")

    blocked_functions = {"LOAD_EXTENSION", "READFILE", "WRITEFILE", "EVAL"}
    for function in statement.find_all(exp.Func):
        function_name = (
            function.name if isinstance(function, exp.Anonymous) else function.sql_name()
        ).upper()
        if function_name in blocked_functions:
            raise ValueError(f"QueryGuard blocked unsafe function '{function_name.lower()}'.")

    cte_names = {
        cte.alias_or_name.lower()
        for cte in statement.find_all(exp.CTE)
        if cte.alias_or_name
    }
    tables = []
    aliases = {}
    for table in statement.find_all(exp.Table):
        table_name = table.name.lower()
        schema_name = table.db.lower() if table.db else None
        catalog_name = table.catalog.lower() if table.catalog else None
        if table_name in cte_names:
            continue
        if table_name.startswith("sqlite_"):
            raise ValueError("QueryGuard blocked access to SQLite metadata tables.")
        if schema_name and schema_name not in ALLOWED_SCHEMAS:
            raise ValueError(f"QueryGuard blocked access to schema '{schema_name}'.")
        if catalog_name:
            raise ValueError("QueryGuard blocked cross-database table access.")
        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"QueryGuard blocked access to table '{table_name}'.")
        tables.append(table_name)
        aliases[table.alias_or_name.lower()] = table_name
        aliases[table_name] = table_name

    if not tables:
        raise ValueError("The query does not reference any approved tables.")

    output_aliases = {
        projection.alias_or_name.lower()
        for select in statement.find_all(exp.Select)
        for projection in select.expressions
        if isinstance(projection, exp.Alias) and projection.alias_or_name
    }
    top_level_select = statement if isinstance(statement, exp.Select) else None
    if top_level_select:
        for projection in top_level_select.expressions:
            if isinstance(projection, exp.Star) or (
                isinstance(projection, exp.Column) and projection.is_star
            ):
                raise ValueError("QueryGuard requires explicit columns; wildcard projections are not allowed.")

    for column in statement.find_all(exp.Column):
        column_name = column.name.lower()
        if column.is_star:
            continue
        qualifier = column.table.lower() if column.table else None
        if qualifier and qualifier in cte_names:
            continue
        if not qualifier and column_name in output_aliases:
            continue
        source_table = aliases.get(qualifier) if qualifier else None
        if source_table:
            allowed = column_name in ALLOWED_COLUMNS[source_table]
        elif qualifier:
            allowed = False
        else:
            allowed = any(column_name in ALLOWED_COLUMNS[table] for table in tables)
        if not allowed:
            raise ValueError(f"QueryGuard blocked access to column '{column_name}'.")

    limit = statement.args.get("limit")
    if limit:
        limit_expression = limit.expression
        if not isinstance(limit_expression, exp.Literal) or limit_expression.is_string:
            raise ValueError("QueryGuard requires LIMIT to be a positive integer.")
        try:
            requested_limit = int(limit_expression.this)
        except (TypeError, ValueError):
            raise ValueError("QueryGuard requires LIMIT to be a positive integer.") from None
        if requested_limit < 1:
            raise ValueError("QueryGuard requires LIMIT to be a positive integer.")
    else:
        requested_limit = MAX_ROWS

    statement = statement.limit(min(requested_limit, MAX_ROWS), copy=False)
    normalized_sql = statement.sql(dialect="sqlite")

    return {
        "statement": statement,
        "tables": sorted(set(tables)),
        "normalized_sql": normalized_sql,
        "max_rows": MAX_ROWS,
        "timeout_seconds": QUERY_TIMEOUT_SECONDS,
        "approved": True,
    }
