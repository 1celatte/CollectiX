import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    if not SECRET_KEY:
        if os.getenv("APP_ENV", "development").lower() == "production":
            raise RuntimeError("Set SECRET_KEY for production.")
        SECRET_KEY = "dev-secret-key"

    SQLALCHEMY_DATABASE_URI = "sqlite:///collectix.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

   # Gmail API sender
   
    GMAIL_SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL")