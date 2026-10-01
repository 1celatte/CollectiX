import unicodedata

from flask_mail import Message
from flask_login import current_user
from app.extensions import mail
from app.models import User

#==============================================================================================================================

#Normalize text for consistent searching and comparison (for prevent duplicates item and collection)

#==============================================================================================================================

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
    admins = User.query.filter_by(role="admin").all()

    if not admins:
        return

    admin_emails = [admin.email for admin in admins]

    msg = Message(
        subject="New Submission - CollectiX",
        recipients=admin_emails
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
