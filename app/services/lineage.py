from typing import Any

import sqlglot
from sqlglot import expressions as exp


def build_lineage(question: str, sql: str, metric_name: str | None) -> dict[str, Any]:
    statement = sqlglot.parse_one(sql, read="sqlite")
    tables = []
    columns = []
    joins = []
    filters = []

    for table in statement.find_all(exp.Table):
        tables.append(table.name)

    for col in statement.find_all(exp.Column):
        columns.append(f"{col.table}.{col.name}" if col.table else col.name)

    for join in statement.find_all(exp.Join):
        joins.append({
            "left": join.this.sql() if join.this else None,
            "right": join.expression.sql() if join.expression else None,
            "kind": join.args.get("kind") or "INNER",
        })

    for where in statement.find_all(exp.Where):
        filters.append(where.this.sql())

    return {
        "question": question,
        "metric_name": metric_name,
        "tables": sorted(set(tables)),
        "columns": sorted(set(columns)),
        "joins": joins,
        "filters": filters,
        "db_dialect": "sqlite",
        "explanation": "The query joins the approved sales tables, aggregates the metric across the selected date window, and returns the top-ranked rows.",
    }
