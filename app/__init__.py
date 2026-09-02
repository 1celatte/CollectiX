from flask import Flask, render_template
from app.extensions import db, login_manager
from flask_migrate import Migrate
from config import Config


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Connect SQLAlchemy to Flask
    db.init_app(app)

    # Connect Flask-Migrate to SQLAlchemy
    Migrate(app, db)

    # Connect Flask-Login to Flask
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Import models so SQLAlchemy knows all the tables
    from app import models
    from app.models import User

    # Tell Flask-Login how to load a user
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Auth Blueprint
    from app.auth import auth
    app.register_blueprint(auth)

    # Register the Browse Blueprint
    from app.browse import browse_bp
    app.register_blueprint(browse_bp)

    @app.route("/")
    def home():
        return render_template("main/index.html")

    return app