class Config:
    SECRET_KEY = "dev-secret-key"

    SQLALCHEMY_DATABASE_URI = "sqlite:///collectix.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False