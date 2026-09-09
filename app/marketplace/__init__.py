from flask import Blueprint

marketplace_bp = Blueprint(
    "marketplace",
    __name__,
    url_prefix="/marketplace",
    template_folder="template"
)

from app.marketplace import routes