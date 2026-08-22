from flask import Flask
from app.extensions import db


def create_app():
    app = Flask(__name__)

    # Basic configuration
    app.config["SECRET_KEY"] = "dev-secret-key"

    # SQLite database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///collectix.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Connect SQLAlchemy to Flask
    db.init_app(app)

    # Import models so SQLAlchemy knows all the tables
    from app import models

    # Create database tables
    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return "CollectiX Database is working!"

    return app