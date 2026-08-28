from flask import Flask
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
    
     # Import models so SQLAlchemy knows about them
    from app.models import User, Collection, Item

    # Register collection routes
    from app.collection.feature import collection_bp
    app.register_blueprint(collection_bp)
    from app.models import User

    # Tell Flask-Login how to load a user
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Auth Blueprint
    from app.auth import auth
    app.register_blueprint(auth)

    @app.route("/")
    def home():
        return "CollectiX Database is working!"

    return app