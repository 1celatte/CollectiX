from flask import Blueprint

browse_bp = Blueprint(
    "browse",
    __name__,
    url_prefix="/browse"  #all routes start with /browse
)

from app.browse import routes