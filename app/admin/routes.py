from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from app.utils import normalize_text

from . import admin
from app.models import Collection,Item, Submission, User, Tag, OwnedItem, Listing, Transaction, Trade
from app.extensions import db

@admin.route("/admin")
@login_required
def admin_home():

    if current_user.role != "admin":
        return "Access denied.", 403 

    return redirect(url_for("admin.users"))


@admin.context_processor
def inject_admin_counts():

    if current_user.is_authenticated and current_user.role == "admin":

        pending_count = Submission.query.filter_by(
            status="pending"
        ).count()

    else:

        pending_count = 0

    return dict(
        pending_count=pending_count
    )


@admin.route("/admin/collections")
@login_required
def collections():

    if current_user.role != "admin":
        return "Access denied.", 403

    collections = Collection.query.all()

    return render_template("collections.html", collections = collections)


@admin.route("/admin/collections/<int:collection_id>")
@login_required
def collection_items(collection_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    collection = Collection.query.get_or_404(collection_id)

    items = Item.query.filter_by(collection_id=collection.id).all()

    return render_template(
        "collection_items.html",
        collection=collection,
        items=items
    )


@admin.route("/admin/collections/<int:collection_id>/edit", methods=["GET", "POST"])
@login_required
def edit_collection(collection_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    collection = Collection.query.get_or_404(collection_id)

    tags = Tag.query.order_by(Tag.name).all()

    if request.method == "POST":
        collection.name = request.form["name"]
        collection.description = request.form["description"]
        tag_id = request.form.get("tag_id")

        if tag_id:
            collection.tag_id = int(tag_id)

        remove_image = request.form.get("remove_image")

        if remove_image == "1" and collection.image:

            image_path = os.path.join(
                os.path.dirname(
                    os.path.dirname(__file__)
                ),
                "collection",
                "static",
                "uploads",
                collection.image
            )

            if os.path.exists(image_path):
                os.remove(image_path)

            collection.image = None

        image_file = request.files.get("image")

        if image_file and image_file.filename:

            image_filename = secure_filename(
                image_file.filename
            )

            upload_folder = os.path.join(
                os.path.dirname(
                    os.path.dirname(__file__)
                ),
                "collection",
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

            collection.image = image_filename

        db.session.commit()

        return redirect(url_for("admin.collections"))

    return render_template(
        "edit_collection.html",
        collection=collection,
        tags=tags
    )


@admin.route("/admin/collections/<int:collection_id>/remove", methods=["POST"])
@login_required
def remove_collection(collection_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    collection = Collection.query.get_or_404(collection_id)

    db.session.delete(collection)
    db.session.commit()

    return redirect(url_for("admin.collections"))


@admin.route("/admin/items/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_item(item_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    item = Item.query.get_or_404(item_id)

    if request.method == "POST":
        item.name = request.form["name"]
        item.description = request.form["description"]

        remove_image = request.form.get("remove_image")

        if remove_image == "1" and item.image:

            image_path = os.path.join(
                os.path.dirname(
                    os.path.dirname(__file__)
                ),
                "collection",
                "static",
                "uploads",
                item.image
            )

            if os.path.exists(image_path):
                os.remove(image_path)

            item.image = None

        image_file = request.files.get("image")

        if image_file and image_file.filename:

            image_filename = secure_filename(
                image_file.filename
            )

            upload_folder = os.path.join(
                os.path.dirname(
                    os.path.dirname(__file__)
                ),
                "collection",
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

            item.image = image_filename

        collection_id = item.collection_id

        db.session.commit()

        return redirect(url_for("admin.collection_items", collection_id=collection_id))

    return render_template(
        "edit_item.html",
        item=item
    )


@admin.route("/admin/items/<int:item_id>/remove", methods=["POST"])
@login_required
def remove_item(item_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    item = Item.query.get_or_404(item_id)

    collection_id = item.collection_id

    db.session.delete(item)
    db.session.commit()

    return redirect(url_for("admin.collection_items", collection_id=collection_id))


@admin.route("/admin/submissions")
@login_required
def submissions():

    if current_user.role != "admin":
        return "Access denied.", 403

    submission_type = request.args.get("type")

    query = Submission.query.filter_by(status="pending")

    if submission_type in ["new_collection", "new_item"]:
        query = query.filter_by(type=submission_type)

    submissions = query.all()

    return render_template(
        "submissions.html", 
        submissions=submissions,
        submission_type=submission_type
        )


@admin.route("/admin/submissions/<int:submission_id>/approve", methods=["POST"])
@login_required
def approve_submission(submission_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    submission = Submission.query.get_or_404(submission_id)

    if submission.type == "new_collection":

        tag_id = submission.tag_id

        if submission.new_tag:

            new_tag = Tag(
                name=submission.new_tag,
                normalized_name=normalize_text(
                    submission.new_tag
                )
            )

            db.session.add(new_tag)
            db.session.flush()

            tag_id = new_tag.id

        collection = Collection(
            name=submission.name,
            normalized_name=normalize_text(
                submission.name
            ),
            tag_id=tag_id,
            description=submission.description,
            image=submission.image,
            status="approved",
            created_by=submission.user_id
        )

        db.session.add(collection)

        db.session.flush()

        submission.collection_id = collection.id
       
    elif submission.type == "new_item":
        item = Item(
            collection_id=submission.collection_id,
            name=submission.name,
            normalized_name=normalize_text(submission.name),
            description=submission.description,
            image=submission.image,
            status="approved",
            created_by=submission.user_id
        )

        db.session.add(item)

    submission.status = "approved"
    submission.reviewed_by = current_user.id

    db.session.commit()

    return redirect(url_for("admin.submissions"))


@admin.route("/admin/submissions/<int:submission_id>/reject", methods=["POST"])
@login_required
def reject_submission(submission_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    submission = Submission.query.get_or_404(submission_id)

    submission.status = "rejected"
    submission.reviewed_by = current_user.id

    db.session.commit()

    return redirect(url_for("admin.submissions"))


@admin.route("/admin/users")
@login_required
def users():

    if current_user.role != "admin":
        return "Access denied.", 403

    users = User.query.filter_by(is_banned=False).all()

    return render_template("users.html", users=users)


@admin.route("/admin/users/<int:user_id>")
@login_required
def user_details(user_id):
    if current_user.role != "admin":
        return "Access denied.", 403

    user = User.query.get_or_404(user_id)

    submissions = Submission.query.filter_by(
        user_id=user.id
    ).order_by(
        Submission.created_at.desc()
    ).all()

    owned_items = OwnedItem.query.filter_by(
        user_id=user.id
    ).all()

    listings = Listing.query.filter_by(
        user_id=user.id
    ).order_by(
        Listing.created_at.desc()
    ).all()

    transactions = Transaction.query.filter(
        (Transaction.buyer_id == user.id) |
        (Transaction.seller_id == user.id)
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    trades = Trade.query.filter(
        (Trade.sender_id == user.id) |
        (Trade.receiver_id == user.id)
    ).order_by(
        Trade.created_at.desc()
    ).all()

    return render_template(
        "user_details.html",
        user=user,
        submissions=submissions,
        owned_items=owned_items,
        listings=listings,
        transactions=transactions,
        trades=trades
    )


@admin.route("/admin/users/banned")
@login_required
def banned_users():
    if current_user.role != "admin":
        return "Access denied.", 403

    users = User.query.filter_by(is_banned=True).all()

    return render_template(
        "banned_users.html",
        users=users
    )


@admin.route("/admin/users/<int:user_id>/ban", methods=["POST"])
@login_required
def ban_user(user_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    user = User.query.get_or_404(user_id)

    if user.role == "admin":
        return "Cannot ban admin user.", 403

    ban_reason = request.form.get("ban_reason", "").strip()

    if not ban_reason:
        return "Ban reason is required.", 400

    user.is_banned = True
    user.ban_reason = ban_reason

    pending_submissions = Submission.query.filter_by(
        user_id=user.id,
        status="pending"
    ).all()

    for submission in pending_submissions:

        submission.status = "rejected"
        submission.reviewed_by = current_user.id

    db.session.commit()

    return redirect(url_for("admin.users"))


@admin.route("/admin/users/<int:user_id>/unban", methods=["POST"])
@login_required
def unban_user(user_id):
    if current_user.role != "admin":
        return "Access denied.", 403

    user = User.query.get_or_404(user_id)

    if user.role == "admin":
        return "Cannot unban admin user.", 403

    user.is_banned = False

    db.session.commit()

    return redirect(url_for("admin.banned_users"))