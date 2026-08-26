from flask import Blueprint, render_template, url_for, redirect, request, flash
from app.extensions import db
from app.models import Collection, Item
from . import collection_bp
import os
from werkzeug.utils import secure_filename


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

@collection_bp.route("/create", methods=["GET", "POST"])
def create_collection():

    if request.method == "POST":

        # Get information from the form
        name = request.form.get("name")
        category = request.form.get("category")
        description = request.form.get("description")

        # Get uploaded image
        image_file = request.files.get("image")

        # Check collection name
        if not name:
            return "Collection name is required."

        # Save image
        image_filename = None

        if image_file and image_file.filename:

            image_filename = secure_filename(
                image_file.filename
            )

            upload_folder = os.path.join(
                collection_bp.root_path,
                "static",
                "uploads"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            image_file.save(
                os.path.join(
                    upload_folder,
                    image_filename
                )
            )

        # Create collection
        collection = Collection(
            name=name,
            category=category,
            description=description,
            image=image_filename,

            # IMPORTANT:
            # New collections need admin approval
            status="pending",

            # Temporary user ID for testing
            created_by=1
        )

        # Save to database
        db.session.add(collection)
        db.session.commit()

        print("NEW COLLECTION ID:", collection.id)
        print("NEW COLLECTION NAME:", collection.name)
        print("NEW COLLECTION STATUS:", collection.status)
        return "Collection submitted successfully! Waiting for admin approval."

    return render_template("create.html")

#=====================================================================================================================

#Create New Collection (goes to pending review by admin).
 
#======================================================================================================================

