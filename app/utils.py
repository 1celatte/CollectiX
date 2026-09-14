import unicodedata

from flask_mail import Message
from flask_login import current_user
from app.extensions import mail
from app.models import User

def normalize_text(text):
    text = text or ""
    text = text.strip()

    normalized = unicodedata.normalize("NFKD", text)

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    ).casefold()


def notify_admin_new_submission(submission):
    admin = User.query.filter_by(role="admin").first()

    if not admin:
        return

    msg = Message(
        subject="New Submission - CollectiX",
        recipients=[admin.email]
    )

    msg.body = f"""
A new submission has been received on CollectiX.

Submitted by: {current_user.name}
Email: {current_user.email}
Type: {submission.type}
Name: {submission.name}

Please log in to the Admin Dashboard to review this submission.
"""

    mail.send(msg)