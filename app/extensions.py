from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

from app.email_service import mail


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()