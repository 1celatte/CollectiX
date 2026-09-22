from flask import render_template, abort, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Collection, UserCollection,OwnedItem, Item,User
from . import my_collection_bp

#=======================================================================================================================

# View all collections saved by the current user
#Track collection progress by calculating the percentage of items owned by the user in each collection

#========================================================================================================================

@my_collection_bp.route("/")
@login_required
def list_my_collections():

    sort = request.args.get("sort", "recent")

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

            # Get all approved items in this collection
            total_items = Item.query.filter_by(
                collection_id=collection.id,
                status="approved"
            ).count()

            # Get items owned by the current user
            owned_item_ids = {
                owned.item_id
                for owned in OwnedItem.query.filter_by(
                    user_id=current_user.id
                ).all()
            }

            # Count only owned items that belong to this collection
            owned_items = Item.query.filter(
                Item.collection_id == collection.id,
                Item.status == "approved",
                Item.id.in_(owned_item_ids)
            ).count() if owned_item_ids else 0

            missing_items = total_items - owned_items

            if total_items > 0:
                progress = round(
                    (owned_items / total_items) * 100
                )
            else:
                progress = 0

            collections.append({
                "collection": collection,
                "total_items": total_items,
                "owned_items": owned_items,
                "missing_items": missing_items,
                "progress": progress
            })


    # Sort collections by progress
    if sort == "progress_asc":
        collections.sort(
            key=lambda data: data["progress"]
        )

    elif sort == "progress_desc":
        collections.sort(
            key=lambda data: data["progress"],
            reverse=True
        )


    return render_template(
        "my.html",
        collections=collections,
        sort=sort
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
        status="approved"
    ).all()

    # Get items owned by the current user
    owned_items = OwnedItem.query.filter_by(
        user_id=current_user.id
    ).all()

    # Calculate collection progress
    total_items = len(items)

    owned_item_ids = {
        owned.item_id
        for owned in owned_items
    }

    owned_count = sum(
        1
        for item in items
        if item.id in owned_item_ids
    )

    missing_items = total_items - owned_count

    if total_items > 0:
        progress = round(
            (owned_count / total_items) * 100
        )
    else:
        progress = 0

    return render_template(
        "detail.html",
        collection=collection,
        items=items,
        owned_items=owned_items,
        total_items=total_items,
        owned_count=owned_count,
        missing_items=missing_items,
        progress=progress
    )

#=======================================================================================================================

# Edit my collection (let useers make items owned or not and set quantity)

#=======================================================================================================================

@my_collection_bp.route(
    "/<int:collection_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_my_collection(collection_id):

    # Check that this collection belongs to the logged-in user
    user_collection = UserCollection.query.filter_by(
        user_id=current_user.id,
        collection_id=collection_id
    ).first()

    if not user_collection:
        abort(404)

    collection = Collection.query.get_or_404(collection_id)

    # Get all approved items in this collection
    items = Item.query.filter_by(
        collection_id=collection_id,
        status="approved"
    ).all()

    # Get items currently owned by the user
    owned_items = OwnedItem.query.filter_by(
        user_id=current_user.id
    ).all()

    if request.method == "POST":

        for item in items:

            # Check whether an OwnedItem record already exists
            owned = OwnedItem.query.filter_by(
                user_id=current_user.id,
                item_id=item.id
            ).first()

            # Check whether the checkbox was checked
            is_owned = request.form.get(
                f"owned_{item.id}"
            )

            # Get the submitted quantity
            quantity = request.form.get(
                f"quantity_{item.id}",
                "0"
            )

            try:
                quantity = int(quantity)
            except ValueError:
                quantity = 0

            if is_owned:
                # Owned items must have quantity >= 1
                if quantity < 1:
                    quantity = 1

                if owned:
                    owned.quantity = quantity
                else:
                    owned = OwnedItem(
                        user_id=current_user.id,
                        item_id=item.id,
                        quantity=quantity
                    )
                    db.session.add(owned)

            else:
                # Unowned items must have quantity = 0
                if owned:
                    db.session.delete(owned)

        db.session.commit()

        flash(
            "Collection updated successfully!",
            "success"
        )

        return redirect(
            url_for(
                "my_collection.view_my_collection",
                collection_id=collection.id
            )
        )

    return render_template(
        "edit.html",
        collection=collection,
        items=items,
        owned_items=owned_items
    )
    
    
#=======================================================================================================================

# Remove Collection from my collection

#=======================================================================================================================

@my_collection_bp.route(
    "/<int:collection_id>/remove",
    methods=["POST"]
)
@login_required
def remove_from_my_collection(collection_id):

    user_collection = UserCollection.query.filter_by(
        user_id=current_user.id,
        collection_id=collection_id
    ).first()

    if not user_collection:
        abort(404)

    db.session.delete(user_collection)
    db.session.commit()

    flash(
        "Collection removed from My Collection.",
        "success"
    )

    return redirect(
        url_for("my_collection.list_my_collections")
    )

#=======================================================================================================================

# Track collection progress

#=======================================================================================================================
