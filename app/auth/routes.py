from flask import render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash

from . import auth
from app.extensions import db
from app.models import User


@auth.route("/test-auth")
def test_auth():
    return "Auth Blueprint is working!"


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Check password confirmation
        if password != confirm_password:
            return "Passwords do not match!"

        # Check whether username already exists
        if User.query.filter_by(username=username).first():
            return "Username already exists!"

        # Check whether email already exists
        if User.query.filter_by(email=email).first():
            return "Email already exists!"

        # Hash password before storing it
        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        return "Registration successful!"

    return render_template("register.html")