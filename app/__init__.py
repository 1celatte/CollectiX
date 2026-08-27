from flask import Flask
from app.extensions import db
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

    # Import models so SQLAlchemy knows all the tables
    from app import models

    @app.route("/")
    def home():
        return "CollectiX Database is working!"

    return app