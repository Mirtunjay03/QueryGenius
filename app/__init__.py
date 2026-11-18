import secrets

from flask import Flask, jsonify, redirect, request, url_for

from app.database import initialize_database
from app.extensions import csrf, db, login_manager
from app.models import User
from app.routes import register_routes


def create_app(config_overrides=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object("app.config")
    if config_overrides:
        app.config.update(config_overrides)
    if app.config["APP_ENV"] == "production" and not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY must be configured when APP_ENV=production.")
    app.config["SECRET_KEY"] = app.config["SECRET_KEY"] or secrets.token_hex(32)
    app.config["DEBUG"] = app.config["APP_ENV"] == "development"
    if "SQLALCHEMY_DATABASE_URI" not in (config_overrides or {}):
        database_url = app.config["APP_DATABASE_URL"]
        if database_url.startswith("mysql://"):
            app.config["SQLALCHEMY_DATABASE_URI"] = database_url.replace(
                "mysql://", "mysql+pymysql://", 1
            )
        else:
            app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/"):
            return jsonify({"error": "Authentication required."}), 401
        return redirect(url_for("login", next=request.url))

    with app.app_context():
        db.create_all()

    initialize_database()
    register_routes(app)
    return app
