from flask import Flask, render_template
from app.extensions import db
from flask_migrate import Migrate


def create_app():
    app = Flask(__name__)

    # Basic configuration
    app.config["SECRET_KEY"] = "dev-secret-key"

    # SQLite database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///collectix.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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