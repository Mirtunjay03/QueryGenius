import sqlite3
import logging
import time
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.config import DB_PATH
from app.database import fetch_metric_definitions, fetch_query_history, insert_query_history
from app.extensions import db
from app.forms import LoginForm
from app.models import User
from app.services.lineage import build_lineage
from app.services.llm_service import generate_sql_with_llm
from app.services.query_engine import analyze_question
from app.services.security import validate_sql_statement

logger = logging.getLogger(__name__)


def _execute_query(sql: str, max_rows: int, timeout_seconds: int):
    database_uri = f"{Path(DB_PATH).as_uri()}?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)
    connection.row_factory = sqlite3.Row
    deadline = time.monotonic() + timeout_seconds
    connection.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
    try:
        connection.execute("PRAGMA query_only = ON")
        cursor = connection.execute(sql)
        columns = [description[0] for description in cursor.description]
        rows = [dict(row) for row in cursor.fetchmany(max_rows)]
        return columns, rows
    finally:
        connection.close()


def register_routes(app: Flask):
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        form = LoginForm()
        if form.validate_on_submit():
            email = form.email.data.strip().lower()
            user = db.session.execute(
                db.select(User).filter_by(email=email)
            ).scalar_one_or_none()
            if user and user.is_active and user.check_password(form.password.data):
                login_user(user, remember=False, fresh=True)
                return redirect(url_for("dashboard"))
            flash("Email or password is incorrect.", "error")
        return render_template("login.html", form=form)

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def dashboard():
        metrics = fetch_metric_definitions()
        history = fetch_query_history(limit=5, user_id=current_user.id)
        return render_template("dashboard.html", metrics=metrics, history=history)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "service": "QueryGenius"})

    @app.route("/api/query", methods=["POST"])
    @login_required
    def api_query():
        payload = request.get_json(silent=True) or {}
        question = request.form.get("question", "") if request.form else ""
        if not question and isinstance(payload, dict):
            question = payload.get("question", "")
        if not isinstance(question, str):
            return jsonify({"error": "The question must be a string."}), 400
        question = question.strip()
        if not question:
            return jsonify({"error": "Please provide a natural-language business question."}), 400
        if len(question) > 2000:
            return jsonify({"error": "Questions must be 2,000 characters or fewer."}), 400

        try:
            analysis = analyze_question(question)
            if analysis.get("ambiguous"):
                return jsonify({"clarification": analysis.get("clarification"), "ambiguous": True}), 400

            generated_sql = generate_sql_with_llm(question, analysis.get("metric_name"))
            validation = validate_sql_statement(generated_sql)
            safe_sql = validation["normalized_sql"]
            columns, rows = _execute_query(
                safe_sql,
                validation["max_rows"],
                validation["timeout_seconds"],
            )
            lineage = build_lineage(question, safe_sql, analysis.get("metric_name"))

            insert_query_history(
                question,
                safe_sql,
                "sqlite",
                analysis.get("metric_name"),
                ",".join(lineage.get("tables", [])),
                lineage.get("explanation", "Generated and verified safely."),
                user_id=current_user.id,
                approved=True,
            )

            return jsonify(
                {
                    "question": question,
                    "metric": analysis.get("metric_name"),
                    "sql": safe_sql,
                    "columns": columns,
                    "rows": rows,
                    "lineage": lineage,
                    "security": {
                        "status": "approved",
                        "max_rows": validation.get("max_rows"),
                        "timeout_seconds": validation.get("timeout_seconds"),
                    },
                }
            )
        except ValueError as exc:
            return jsonify({"error": str(exc), "ambiguous": True if "Would you like" in str(exc) else False}), 400
        except Exception as exc:
            logger.exception("Query generation or execution failed")
            if isinstance(exc, sqlite3.OperationalError) and "interrupted" in str(exc).lower():
                return jsonify({"error": "The query exceeded the execution time limit."}), 504
            return jsonify({"error": "Query generation or execution failed."}), 500
