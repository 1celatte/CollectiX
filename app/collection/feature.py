from flask import Blueprint, render_template, url_for, redirect, request, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Collection, Item, Submission,UserCollection,Tag
from . import collection_bp
import os
from werkzeug.utils import secure_filename
from app.utils import normalize_text

collection_bp = Blueprint(
    "collection",
    __name__,
    url_prefix="/collections",
    template_folder="template",
    static_folder="static",
    static_url_path="/collection-static"
)

#=======================================================================================================================

#list collections in Public collection

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

#==============================================================================================

#View Collection Details

#=======================================================================================================================
    
@collection_bp.route("/<int:collection_id>")
def view_collection(collection_id):

    collection = Collection.query.get_or_404(collection_id)

    # Get only approved items belonging to this collection.
    items = Item.query.filter_by(
        collection_id=collection.id,
        status="approved"
    ).all()

    # Check whether the logged-in user already owns this collection.
    already_in_collection = False

    if current_user.is_authenticated:

        already_in_collection = UserCollection.query.filter_by(
            user_id=current_user.id,
            collection_id=collection.id
        ).first() is not None

    return render_template(
        "view.html",
        collection=collection,
        items=items,
        already_in_collection=already_in_collection
    )
    
# =====================================================================================================

# Create New Collection (goes to pending review by admin).

# =====================================================================================================

@collection_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_collection():

    # Load approved tags for the dropdown.
    tags = Tag.query.order_by(Tag.name).all()

    if request.method == "POST":

        # Get information from the form.
        name = request.form.get("name", "").strip()
        normalized_name = normalize_text(name)

        tag_value = request.form.get("tag_id")
        new_tag = request.form.get("new_tag", "").strip()
        normalized_new_tag = normalize_text(new_tag)

        description = request.form.get("description", "").strip()

        # Check that collection name was provided.
        if not name:

            flash(
                "Collection name is required.",
                "error"
            )

            return render_template(
                "create.html",
                tags=tags
            )

        # Check if collection already exists.
        existing_collection = Collection.query.filter_by(
            normalized_name=normalized_name
        ).first()

        if existing_collection:

            flash(
                "This collection already exists. Please use the existing collection.",
                "error"
            )

            return redirect(
                url_for("collection.list_collections")
            )

        selected_tag_id = None
        requested_new_tag = None

        # -----------------------------------------
        # User selected "Other"
        # -----------------------------------------
        if tag_value == "other":

            if not new_tag:

                flash(
                    "Please enter a name for the new tag.",
                    "error"
                )

                return render_template(
                    "create.html",
                    tags=tags
                )

            # Prevent duplicates among approved tags.
            existing_tag = Tag.query.filter_by(
                normalized_name=normalized_new_tag
            ).first()

            if existing_tag:

                flash(
                    "This tag already exists. Please select it from the list.",
                    "error"
                )

                return render_template(
                    "create.html",
                    tags=tags
                )

            # Prevent duplicate pending tag requests.
            pending_tag_request = Submission.query.filter(
                Submission.status == "pending",
                db.func.lower(Submission.new_tag) == new_tag.lower()
            ).first()

            if pending_tag_request:

                flash(
                    "This new tag is already waiting for admin approval.",
                    "error"
                )

                return render_template(
                    "create.html",
                    tags=tags
                )

            # Do not create a Tag yet.
            # Admin will approve/create it later.
            requested_new_tag = new_tag

        # -----------------------------------------
        # User selected an existing tag
        # -----------------------------------------
        else:

            if not tag_value:

                flash(
                    "Please select a tag.",
                    "error"
                )

                return render_template(
                    "create.html",
                    tags=tags
                )

            try:
                tag_id = int(tag_value)

            except (TypeError, ValueError):

                flash(
                    "The selected tag is not valid.",
                    "error"
                )

                return render_template(
                    "create.html",
                    tags=tags
                )

            selected_tag = db.session.get(
                Tag,
                tag_id
            )

            if not selected_tag:

                flash(
                    "The selected tag is not valid.",
                    "error"
                )

                return render_template(
                    "create.html",
                    tags=tags
                )

            selected_tag_id = selected_tag.id

        # -----------------------------------------
        # Get uploaded image
        # -----------------------------------------
        image_file = request.files.get("image")
        image_filename = None

        # Save image.
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

        # -----------------------------------------
        # Create pending collection
        # -----------------------------------------
        collection = Collection(
            name=name,
            normalized_name=normalized_name,
            tag_id=selected_tag_id,
            description=description,
            image=image_filename,
            status="pending",
            created_by=current_user.id
        )

        db.session.add(collection)

        # Get collection.id before creating Submission.
        db.session.flush()

        # -----------------------------------------
        # Create submission for admin approval
        # -----------------------------------------
        submission = Submission(
            user_id=current_user.id,
            type="new_collection",
            collection_id=collection.id,
            tag_id=selected_tag_id,
            new_tag=requested_new_tag,
            name=name,
            description=description,
            image=image_filename,
            status="pending"
        )

        db.session.add(submission)

        # Save collection + submission.
        db.session.commit()

        flash(
            "Collection submitted successfully! Waiting for admin approval.",
            "success"
        )

        return redirect(
            url_for("collection.list_collections")
        )

    # GET request
    return render_template(
        "create.html",
        tags=tags
    )

#=====================================================================================================================

# Add items to Public Collection (goes to pending review).

#=====================================================================================================================

@collection_bp.route(
    "/<int:collection_id>/add",
    methods=["GET", "POST"]
)
@login_required
def add_item(collection_id):

    collection = Collection.query.get_or_404(collection_id)

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        normalized_name = normalize_text(name)

        description = request.form.get("description", "").strip()

        # Check empty name
        if not name:
            flash(
                "Item name is required.",
                "error"
            )
            return redirect(
                url_for(
                    "collection.add_item",
                    collection_id=collection.id
                )
            )

        # Check if item already exists in THIS collection
        existing_items = Item.query.filter_by(
            collection_id=collection.id
        ).all()

        existing_item = next(
            (
                item
                for item in existing_items
                if normalize_text(item.name) == normalized_name
            ),
            None
        )

        if existing_item:
            flash(
                "This item already exists in this collection.",
                "error"
            )
            return redirect(
                url_for(
                    "collection.add_item",
                    collection_id=collection.id
                )
            )

        # Check pending submissions
        pending_submissions = Submission.query.filter(
            Submission.collection_id == collection.id,
            Submission.type == "new_item",
            Submission.status == "pending"
        ).all()

        existing_submission = next(
            (
                submission
                for submission in pending_submissions
                if normalize_text(submission.name) == normalized_name
            ),
            None
        )

        if existing_submission:
            flash(
                "This item is already waiting for admin approval.",
                "error"
            )
            return redirect(
                url_for(
                    "collection.add_item",
                    collection_id=collection.id
                )
            )

        # ==========================================
        # SAVE IMAGE
        # ==========================================

        image_file = request.files.get("image")
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

        # ==========================================
        # CREATE PENDING SUBMISSION
        # ==========================================

        submission = Submission(
            user_id=current_user.id,
            type="new_item",
            collection_id=collection.id,
            name=name,
            description=description,
            image=image_filename,
            status="pending"
        )

        db.session.add(submission)
        db.session.commit()

        flash(
            "Item submitted successfully. Please wait for admin approval.",
            "success"
        )

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

@collection_bp.route(
    "/<int:collection_id>/add-to-my-collection",
    methods=["POST"]
)
@login_required
def add_to_my_collection(collection_id):

    collection = Collection.query.get_or_404(collection_id)

    # Check whether user already added this collection
    existing = UserCollection.query.filter_by(
        user_id=current_user.id,
        collection_id=collection.id
    ).first()

    if existing:

        flash(
            "This collection is already in My Collection.",
            "error"
        )

        return redirect(
            url_for(
                "collection.view_collection",
                collection_id=collection.id
            )
        )

    # Add collection to My Collection
    user_collection = UserCollection(
        user_id=current_user.id,
        collection_id=collection.id
    )

    db.session.add(user_collection)
    db.session.commit()

    flash(
        "Collection added to My Collection successfully!",
        "success"
    )

    return redirect(
        url_for(
            "collection.view_collection",
            collection_id=collection.id
        )
    )