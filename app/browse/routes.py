from flask import render_template
from app.browse import browse_bp

@browse_bp.route("/")
def index():
    #Temporary response for testing
    return render_template("browse/browse.html")