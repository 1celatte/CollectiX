from flask import Blueprint

browse_bp = Blueprint(
    "browse",
    __name__,
    url_prefix="/browse",  #all routes start with /browse
    template_folder="template"  #browse HTML files that are inside app/browse/template
)

from app.browse import routes