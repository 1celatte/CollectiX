from flask import Blueprint

my_collection_bp = Blueprint(
    "my_collection",
    __name__,
    url_prefix="/my-collections",
    template_folder="templates"
)