from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = "login"
login_manager.login_message = "Please sign in to access QueryGenius."
login_manager.login_message_category = "info"
