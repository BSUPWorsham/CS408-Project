import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to view that page."
login_manager.login_message_category = "warning"


def create_app(test_config=None):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app = Flask(
        __name__,
        instance_path=os.path.join(base_dir, "instance"),  # matches configure.sh (app/instance)
    )
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        SQLALCHEMY_DATABASE_URI="sqlite:///aplin.db",  # stored in app/instance/aplin.db
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        PDF_FOLDER=os.path.join(base_dir, "static", "uploads", "pdfs"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["PDF_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models
    from app.public import public
    from app.auth import auth
    from app.admin import admin

    app.register_blueprint(public)
    app.register_blueprint(auth)
    app.register_blueprint(admin)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(models.User, int(user_id))
        except (TypeError, ValueError):
            return None

    return app
