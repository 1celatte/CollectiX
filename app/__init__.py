from flask import Flask, render_template, redirect, request, url_for
from app.extensions import db, login_manager,mail
import flask_migrate
from config import Config


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Connect Flask-Mail to Flask
    mail.init_app(app)

    # Connect SQLAlchemy to Flask
    db.init_app(app)

    # Connect Flask-Migrate to SQLAlchemy
    flask_migrate.Migrate(app, db)

    # Connect Flask-Login to Flask
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Import models so SQLAlchemy knows all the tables
    from app import models

    from app.models import User, Collection, Item

    # Register collection routes
    from app.collection.feature import collection_bp
    app.register_blueprint(collection_bp)

    # Register my-collections routes
    from app.mycollection.feature import my_collection_bp
    app.register_blueprint(my_collection_bp)

    # Tell Flask-Login how to load a user
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Custom behavior when a logged-out user tries
    # to add a collection to My Collection.
    @login_manager.unauthorized_handler
    def unauthorized():
        if (
            request.method == "POST"
            and request.path.endswith("/add-to-my-collection")
        ):
            collection_id = request.view_args.get("collection_id")

            return redirect(
                url_for(
                    "auth.login",
                    next=url_for(
                        "collection.view_collection",
                        collection_id=collection_id
                    )
                )
            )

        # Normal behavior for other protected routes.
        return redirect(
            url_for(
                "auth.login",
                next=request.full_path
            )
        )

    # Register Auth Blueprint
    from app.auth import auth
    app.register_blueprint(auth)

    # Register the Browse Blueprint
    from app.browse import browse_bp
    app.register_blueprint(browse_bp)
    
    # Register the Marketplace Blueprint
    from app.marketplace import marketplace_bp
    app.register_blueprint(marketplace_bp)

    @app.route("/")
    def home():
        return render_template("main/index.html")

    return app