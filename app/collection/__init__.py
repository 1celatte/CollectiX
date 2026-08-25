from flask import Blueprint

collection_bp = Blueprint(
    "collection",
    __name__,
    url_prefix="/collections",
    template_folder="template"
)