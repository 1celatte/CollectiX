from flask import render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os

from . import auth
from app.extensions import db
from app.models import User


@auth.route("/test-auth")
def test_auth():
    return "Auth Blueprint is working!"


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        email_error = None
        password_error = None

        # Check whether email already exists
        if User.query.filter_by(email=email).first():
            email_error = "Email already exists."

        # Check password confirmation
        if password != confirm_password:
            password_error = "Passwords do not match."

        # If there are errors, stay on Register page
        if email_error or password_error:
            return render_template(
                "register.html",
                name=name,
                email=email,
                email_error=email_error,
                password_error=password_error
            )

        # Hash password before storing it
        hashed_password = generate_password_hash(password)

        user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        # Invalid email
        if user is None:
            return render_template(
                "login.html",
                login_error="Invalid email or password.",
                email=email
            )

        # Incorrect password
        if not check_password_hash(user.password, password):
            return render_template(
                "login.html",
                login_error="Invalid email or password.",
                email=email
            )

        login_user(user)

        next_page = request.args.get("next")

        if next_page:
            return redirect(next_page)

        return redirect(url_for("home"))

    return render_template("login.html")


@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@auth.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@auth.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        profile_picture = request.files.get("profile_picture")
        remove_profile_picture = request.form.get("remove_profile_picture") == "1"

        email_error = None

        existing_email = User.query.filter(
            (User.email == email) &
            (User.id != current_user.id)
        ).first()

        if existing_email:
            email_error = "Email already exists."

        if email_error:
            return render_template(
                "edit_profile.html",
                name=name,
                email=email,
                email_error=email_error
            )

        # Remove profile picture
        if remove_profile_picture:
            if current_user.profile_picture:
                file_path = os.path.join(
                    auth.static_folder,
                    current_user.profile_picture
                )

                if os.path.exists(file_path):
                    os.remove(file_path)

            current_user.profile_picture = None

        # Upload new profile picture   
        elif profile_picture and profile_picture.filename:
            filename = f"{current_user.id}_{secure_filename(profile_picture.filename)}"

            upload_folder = os.path.join(
                auth.static_folder,
                "uploads",
                "avatars"
            )

            os.makedirs(upload_folder, exist_ok=True)

            profile_picture.save(
                os.path.join(upload_folder, filename)
            )

            current_user.profile_picture = f"uploads/avatars/{filename}"

        current_user.name = name
        current_user.email = email

        db.session.commit()

        return redirect(url_for("auth.profile"))

    return render_template("edit_profile.html")


@auth.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not check_password_hash(current_user.password, current_password):
        return render_template(
            "edit_profile.html",
            password_error="Current password is incorrect."
        )
    
    if new_password != confirm_password:
        return render_template(
        "edit_profile.html",
        confirm_password_error="New password and confirm password do not match."
        )

    current_user.password = generate_password_hash(new_password)

    db.session.commit()

    return redirect(url_for("auth.profile"))


@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")

        user = User.query.filter_by(email=email).first()

        if user is None:
            return render_template(
                "forgot_password.html",
                email=email,
                email_error="Email does not exist."
            )

        return redirect(url_for("auth.reset_password", email=email))

    return render_template("forgot_password.html")


@auth.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    email = request.args.get("email")

    user = User.query.filter_by(email=email).first()

    if user is None:
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            return render_template(
                "reset_password.html",
                password_error="New password and confirm password do not match."
            )

        user.password = generate_password_hash(new_password)

        db.session.commit()

        return redirect(url_for("auth.login"))

    return render_template("reset_password.html")