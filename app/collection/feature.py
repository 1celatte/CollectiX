from flask import Blueprint, render_template, url_for, redirect, request, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Collection, Item, Submission
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

    collection = Collection.query.get_or_404(collection_id)

    # Get only approved items belonging to this collection
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

#Create New Collection (goes to pending review by admin).

#=================================================================================================================

@collection_bp.route("/create", methods=["GET", "POST"])
def create_collection():

    if request.method == "POST":

        # Get information from form
        name = request.form.get("name")
        category = request.form.get("category")
        description = request.form.get("description")

        # Check if collection already exists
        existing_collection = Collection.query.filter_by(
            name=name
        ).first()

        if existing_collection:
            return "This collection already exists. Please use the existing collection."

        # Get uploaded image
        image_file = request.files.get("image")

        image_filename = None

        # Save image
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

        # Create new collection
        collection = Collection(
            name=name,
            category=category,
            description=description,
            image=image_filename,
            status="pending",

            # Temporary testing value(will replace with current user id later)
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

#Add items to Public Collection (goes to pending review).
 
#======================================================================================================================

@collection_bp.route("/<int:collection_id>/add", methods=["GET", "POST"])
@login_required
def add_item(collection_id):

    collection = Collection.query.get_or_404(collection_id)

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        # Check empty name
        if not name:
            flash("Item name is required.")
            return redirect(
                url_for(
                    "collection.add_item",
                    collection_id=collection.id
                )
            )

        # Check if item already exists
        existing_item = Item.query.filter(
            Item.collection_id == collection.id,
            db.func.lower(Item.name) == name.lower()
        ).first()

        if existing_item:
            flash("This item already exists in this collection.")
            return redirect(
                url_for(
                    "collection.add_item",
                    collection_id=collection.id
                )
            )

        # Check if someone has already submitted the same item
        existing_submission = Submission.query.filter(
            Submission.collection_id == collection.id,
            Submission.type == "new_item",
            db.func.lower(Submission.name) == name.lower(),
            Submission.status == "pending"
        ).first()

        if existing_submission:
            flash("This item is already waiting for admin approval.")
            return redirect(
                url_for(
                    "collection.add_item",
                    collection_id=collection.id
                )
            )

        # Create pending submission
        submission = Submission(
            user_id=current_user.id,
            type="new_item",
            collection_id=collection.id,
            name=name,
            description=description,
            status="pending"
        )

        db.session.add(submission)
        db.session.commit()

        flash("Item submitted successfully. Please wait for admin approval.")

        return redirect(
            url_for(
                "collection.view_collection",
                collection_id=collection.id
            )
        )

    return render_template(
        "item.html",
        collection=collection
    )


#================================================================================================================

#Add Public Collection to My collection

#=================================================================================================================
