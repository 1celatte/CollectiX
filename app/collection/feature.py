from flask import Blueprint, render_template

from app.models import Collection,Item
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

#list collectionsin Public collection

#========================================================================================================================

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

#==============================================================================================

#View Collection Details

#=======================================================================================================================
    
@collection_bp.route("/<int:collection_id>")
def view_collection(collection_id):

    collection = Collection.query.filter_by(
        id=collection_id,
        status="approved"
    ).first_or_404()

    items = Item.query.filter_by(
        collection_id=collection.id,
        status="approved"
    ).all()

    return render_template(
        "view.html",
        collection=collection,
        items=items
    )

#================================================================================================================

#Add items to Public Collection (goes to pending review).

#=================================================================================================================

#=====================================================================================================================

#Create New Collection (goes to pending review by admin).
 
#======================================================================================================================

