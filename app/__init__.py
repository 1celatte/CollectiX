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
    
     # Import models so SQLAlchemy knows about them
    from app.models import User, Collection, Item

    # Register collection routes
    from app.collection.feature import collection_bp
    app.register_blueprint(collection_bp)

    @app.route("/")
    def home():
        return "CollectiX Database is working!"

    return app