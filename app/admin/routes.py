from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user

from . import admin
from app.models import Collection,Item, Submission, User
from app.extensions import db

@admin.route("/admin")
@login_required
def dashboard():

    if current_user.role != "admin":
        return "Access denied.", 403 

    return render_template("dashboard.html")


@admin.route("/admin/collections")
@login_required
def collections():

    if current_user.role != "admin":
        return "Access denied.", 403

    collections = Collection.query.all()

    return render_template("collections.html", collections = collections)


@admin.route("/admin/collections/<int:collection_id>/edit", methods=["GET", "POST"])
@login_required
def edit_collection(collection_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    collection = Collection.query.get_or_404(collection_id)

    if request.method == "POST":
        collection.name = request.form["name"]
        collection.description = request.form["description"]

        db.session.commit()

        return redirect(url_for("admin.collections"))

    return render_template(
        "edit_collection.html",
        collection=collection
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


@admin.route("/admin/items")
@login_required
def items():

    if current_user.role != "admin":
        return "Access denied.", 403

    items = Item.query.all()

    return render_template("admin_items.html", items=items)


@admin.route("/admin/items/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_item(item_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    item = Item.query.get_or_404(item_id)

    if request.method == "POST":
        item.name = request.form["name"]
        item.description = request.form["description"]

        db.session.commit()

        return redirect(url_for("admin.items"))

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

    db.session.delete(item)
    db.session.commit()

    return redirect(url_for("admin.items"))


@admin.route("/admin/collections/<int:collection_id>/approve", methods=["POST"])
@login_required
def approve_collection(collection_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    collection = Collection.query.get_or_404(collection_id)

    collection.status = "approved"

    db.session.commit()

    return redirect(url_for("admin.collections"))


@admin.route("/admin/submissions")
@login_required
def submissions():

    if current_user.role != "admin":
        return "Access denied.", 403

    submissions = Submission.query.filter_by(status="pending").all()

    return render_template("submissions.html", submissions=submissions)


@admin.route("/admin/submissions/<int:submission_id>/approve", methods=["POST"])
@login_required
def approve_submission(submission_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    submission = Submission.query.get_or_404(submission_id)

    if submission.type == "new_collection":
        collection = Collection(
            name=submission.name,
            description=submission.description,
            image=submission.image,
            status="approved",
            created_by=submission.user_id
        )

        db.session.add(collection)

    elif submission.type == "new_item":
        item = Item(
        collection_id=submission.collection_id,
        name=submission.name,
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

    users = User.query.all()

    return render_template("users.html", users=users)


@admin.route("/admin/users/<int:user_id>/remove", methods=["POST"])
@login_required
def remove_user(user_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    user = User.query.get_or_404(user_id)

    if user.role == "admin":
        return "Cannot delete admin user.", 403

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for("admin.users"))