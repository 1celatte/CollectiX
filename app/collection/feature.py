from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Collection, Item, UserCollection
from ..utils import save_upload

collections_bp = Blueprint("collections", __name__, url_prefix="/collections")


#=======================================================================================================================

#list & view collections and items in collection

#========================================================================================================================

@collections_bp.route("/")
def list_collections():
    query = request.args.get("q", "").strip()
    q = Collection.query.filter_by(status="approved")
    if query:
        q = q.filter(Collection.name.ilike(f"%{query}%"))
    collections = q.order_by(Collection.name.asc()).all()
    return render_template("collections/list.html", collections=collections, query=query)


@collections_bp.route("/<int:collection_id>")
def view_collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    items = Item.query.filter_by(collection_id=collection.id, status="approved").all()
    already_added = False
    if current_user.is_authenticated:
        already_added = UserCollection.query.filter_by(
            user_id=current_user.id, collection_id=collection.id).first() is not None
    return render_template("collections/view.html", collection=collection, items=items,
                            already_added=already_added)
    
#==============================================================================================

 #Create New Collection (goes to pending review by admin).
 
#==============================================================================================
    
@collections_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_collection():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "")
        category = request.form.get("category", "General")
        image_file = request.files.get("image")

        if not name:
            flash("Collection name is required.", "danger")
            return render_template("collections/create.html")

        image_filename = save_upload(image_file, default="default_collection.png")
        collection = Collection(name=name, description=description, category=category,
                                 image=image_filename, status="pending",
                                 created_by=current_user.id)
        db.session.add(collection)
        db.session.commit()
        flash("Collection submitted sucessfully! It will appear once approved by an admin.", "success")
        return redirect(url_for("collections.list_collections"))

    return render_template("collections/create.html")

#================================================================================================================

#Add items to Public Collection (goes to pending review).

#=================================================================================================================

@collections_bp.route("/<int:collection_id>/add-item", methods=["GET", "POST"])
@login_required
def add_item(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "")
        image_file = request.files.get("image")

        if not name:
            flash("Item name is required.", "danger")
            return render_template("collections/add.html", collection=collection)

        image_filename = save_upload(image_file, default="default_item.png")
        item = Item(collection_id=collection.id, name=name, description=description,
                    image=image_filename, status="pending", created_by=current_user.id)
        db.session.add(item)
        db.session.commit()
        flash("Item submitted! It will appear once approved by an admin.", "success")
        return redirect(url_for("collections.view_collection", collection_id=collection.id))

    return render_template("collections/add.html", collection=collection)

#=====================================================================================================================

#add collection to user's personal collection

#======================================================================================================================

@collections_bp.route("/<int:collection_id>/add-to-my-collection", methods=["POST"])
@login_required
def add_to_my_collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    existing = UserCollection.query.filter_by(
        user_id=current_user.id, collection_id=collection.id).first()
    if existing:
        flash("You already added this collection.", "info")
    else:
        uc = UserCollection(user_id=current_user.id, collection_id=collection.id)
        db.session.add(uc)
        db.session.commit()
        flash(f"'{collection.name}' added to your collection!", "success")
    return redirect(url_for("", collection_id=collection.id))
