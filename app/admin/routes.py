from flask import render_template, redirect, url_for
from flask_login import login_required, current_user

from . import admin
from app.models import Collection
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


@admin.route("/admin/collections/<int:collection_id>/approve", methods=["POST"])
@login_required
def approve_collection(collection_id):

    if current_user.role != "admin":
        return "Access denied.", 403

    collection = Collection.query.get_or_404(collection_id)

    collection.status = "approved"

    db.session.commit()

    return redirect(url_for("admin.collections"))