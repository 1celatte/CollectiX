from flask import Flask, render_template
from app.extensions import db
from flask_migrate import Migrate
from config import Config


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Connect SQLAlchemy to Flask
    db.init_app(app)
    # Register the Browse Blueprint
    from app.browse import browse_bp
    app.register_blueprint(browse_bp)

    # Connect Flask-Migrate to SQLAlchemy
    Migrate(app, db)

    # Import models so SQLAlchemy knows all the tables
    from app import models

    @app.route("/")
    def home():
        return render_template("main/index.html")

    return app