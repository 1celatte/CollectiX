from flask import render_template, request, redirect, url_for
from datetime import datetime, timedelta
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from flask_mail import Message
import os

from . import auth
from app.extensions import db, mail
from app.models import User


def validate_password(password): 
    if (
        len(password) < 8
        or not any(char.isupper() for char in password)
        or not any(char.islower() for char in password)
        or not any(char.isdigit() for char in password)
        or not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for char in password)
    ):
        return "Password must be at least 8 characters and contain uppercase, lowercase, number, and special character."

    return None


@auth.route("/test-auth")
def test_auth():
    return "Auth Blueprint is working!"

@auth.route("/test-email")
def test_email():
    msg = Message(
        subject="CollectiX Email Test",
        sender=mail.username,
        recipients=["cngchifei@gmail.com"]
    )

    msg.body = "This is a test email from CollectiX."

    mail.send(msg)

    return "Test email sent!"

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
        existing_user = User.query.filter_by(email=email).first()

        if existing_user and existing_user.email_verified:
            email_error = "Email already exists."

        # Check password requirements
        password_error = validate_password(password)

        # Check password confirmation
        if not password_error and password != confirm_password:
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

        # Generate verification token
        verification_token = secrets.token_urlsafe(32)

        # Token expires after 30 minutes
        verification_expires_at = datetime.utcnow() + timedelta(minutes=30)

        # Hash password before storing it
        hashed_password = generate_password_hash(password)

        # If the email already exists but is not verified,
        # update the existing account
        if existing_user:
            user = existing_user

            user.name = name
            user.password = hashed_password
            user.email_verified = False
            user.email_verification_token = verification_token
            user.email_verification_expires_at = verification_expires_at

        # If the email does not exist,
        # create a new account
        else:
            user = User(
                name=name,
                email=email,
                password=hashed_password,
                email_verified=False,
                email_verification_token=verification_token,
                email_verification_expires_at=verification_expires_at
            )

            db.session.add(user)
            
        db.session.commit()

        # Create verification link
        verification_link = url_for(
            "auth.verify_email",
            token=verification_token,
            _external=True
        )

        # Create email
        msg = Message(
            subject="Verify your CollectiX account",
            recipients=[email]
        )

        # Email content is stored in HTML template
        msg.html = render_template(
            "verify_email.html",
            name=name,
            verification_link=verification_link
        )

        mail.send(msg)

        return redirect(url_for("auth.check_email"))

    return render_template("register.html")


@auth.route("/verify-email/<token>")
def verify_email(token):
    user = User.query.filter_by(
        email_verification_token=token
    ).first()

    # Token does not exist
    if user is None:
        return "Invalid verification link."

    # Check whether token has expired
    if (
        user.email_verification_expires_at is None
        or datetime.utcnow() > user.email_verification_expires_at
    ):
        return "Verification link has expired."

    return render_template(
        "confirm_email.html",
        token=token,
        email=user.email
    )    


@auth.route("/confirm-email/<token>", methods=["POST"])
def confirm_email(token):
    user = User.query.filter_by(
        email_verification_token=token
    ).first()

    # Token does not exist
    if user is None:
        return "Invalid verification link."

    # Check whether token has expired
    if (
        user.email_verification_expires_at is None
        or datetime.utcnow() > user.email_verification_expires_at
    ):
        return "Verification link has expired."

    # Verify email
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expires_at = None

    db.session.commit()

    return render_template(
        "email_verified.html",
        email=user.email
    )


@auth.route("/check-email")
def check_email():
    return render_template("check_email.html")


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

        # Email not verified
        if not user.email_verified:
            return render_template(
                "login.html",
                login_error="Please verify your email before logging in. Check your inbox for the verification email.",
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
        profile_picture = request.files.get("profile_picture")
        remove_profile_picture = request.form.get("remove_profile_picture") == "1"

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
            current_password_error="Current password is incorrect."
        )

    password_error = validate_password(new_password)

    if password_error:
        return render_template(
            "edit_profile.html",
            password_error=password_error
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

        # Generate password reset token
        reset_token = secrets.token_urlsafe(32)

        # Token expires after 30 minutes
        reset_expires_at = datetime.utcnow() + timedelta(minutes=30)

        # Save reset token to the user
        user.password_reset_token = reset_token
        user.password_reset_expires_at = reset_expires_at

        db.session.commit()

        # Create password reset link
        reset_link = url_for(
            "auth.reset_password",
            token=reset_token,
            _external=True
        )

        # Create reset password email
        msg = Message(
            subject="Reset your CollectiX password",
            recipients=[email]
        )

        msg.html = render_template(
            "reset_password_email.html",
            name=user.name,
            reset_link=reset_link
        )

        mail.send(msg)

        return redirect(url_for("auth.check_reset_email"))

    return render_template("forgot_password.html")


@auth.route("/check-reset-email")
def check_reset_email():
    return render_template("check_reset_email.html")


@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(
        password_reset_token=token
    ).first()

    # Token does not exist
    if user is None:
        return "Invalid password reset link."

    # Check whether token has expired
    if (
        user.password_reset_expires_at is None
        or datetime.utcnow() > user.password_reset_expires_at
    ):
        return "Password reset link has expired."

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        password_error = validate_password(new_password)

        if password_error:
            return render_template(
                "reset_password.html",
                password_error=password_error
            )

        if new_password != confirm_password:
            return render_template(
                "reset_password.html",
                password_error="New password and confirm password do not match."
            )

        user.password = generate_password_hash(new_password)

        # Clear reset token after successful password reset
        user.password_reset_token = None
        user.password_reset_expires_at = None

        db.session.commit()

        return redirect(url_for("auth.login"))

    return render_template("reset_password.html")