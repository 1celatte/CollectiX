from flask import Blueprint, render_template

from app.models import Collection
from . import collection_bp


collection_bp = Blueprint(
    "collection",
    __name__,
    url_prefix="/collections",
    template_folder="template",
    static_folder="static",
    static_url_path="/collection-static"
)

#=======================================================================================================================

#list & view collections and items in collection

#========================================================================================================================

#list
@collection_bp.route("/")
def list_collections():

    collections = Collection.query.filter_by(
        status="approved"
    ).all()

    return render_template(
        "list.html",
        collections=collections
    )

@collection_bp.route("/test")
def create_test_collection():

    collection = Collection(
        name="Pokemon TCG",
        category="Trading Cards",
        description="A test collection for Pokemon trading cards.",
        image="test.png",
        status="approved",
        created_by=1
    )

    from app.extensions import db

    db.session.add(collection)
    db.session.commit()

    return "Test collection created!"

@collection_bp.route("/fix-images")
def fix_images():

    collections = Collection.query.all()

    for collection in collections:
        collection.image = "test.png"

    db.session.commit()

    return "All collection images updated!"

#==============================================================================================

 #Create New Collection (goes to pending review by admin).
 
#=======================================================================================================================
    


#================================================================================================================

#Add items to Public Collection (goes to pending review).

#=================================================================================================================

#=====================================================================================================================

#add collection to user's personal collection

#======================================================================================================================

