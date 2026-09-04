from flask import render_template, abort
from flask_login import login_required, current_user

from app.models import Collection, UserCollection,OwnedItem, Item
from . import my_collection_bp

#=======================================================================================================================

# View all collections saved by the current user

#========================================================================================================================

@my_collection_bp.route("/")
@login_required
def list_my_collections():

    user_collections = UserCollection.query.filter_by(
        user_id=current_user.id
    ).order_by(
        UserCollection.added_at.desc()
    ).all()

    collections = []

    for user_collection in user_collections:

        collection = Collection.query.get(
            user_collection.collection_id
        )

        if collection:
            collections.append(collection)

    return render_template(
        "my.html",
        collections=collections
    )
    
#=======================================================================================================================

# View collection's details

#=======================================================================================================================

@my_collection_bp.route("/<int:collection_id>")
@login_required
def view_my_collection(collection_id):

    # Check that this collection belongs to the logged-in user
    user_collection = UserCollection.query.filter_by(
        user_id=current_user.id,
        collection_id=collection_id
    ).first()

    # User must not access another user's saved collection page
    if not user_collection:
        abort(404)

    # Get the collection
    collection = Collection.query.get_or_404(
        collection_id
    )

    # Get all approved items inside this collection
    items = Item.query.filter_by(
        collection_id=collection_id,
    ).all()

    # Get items owned by the current user
    owned_items = OwnedItem.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "detail.html",
        collection=collection,
        items=items,
        owned_items=owned_items
    )












