import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage as MimeEmailMessage
from pathlib import Path

from flask import current_app


GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


class Message:
    """Small message container compatible with this project's mail usage."""

    def __init__(self, subject, recipients, sender=None):
        self.subject = subject
        self.recipients = list(recipients or [])
        self.sender = sender
        self.body = None
        self.html = None


class GmailMailer:
    def init_app(self, app):
        app.extensions["gmail_mailer"] = self

    def send(self, message):
        sender = (
            message.sender
            or current_app.config.get("GMAIL_SENDER_EMAIL")
        )

        if not sender:
            raise RuntimeError("Set GMAIL_SENDER_EMAIL in the environment.")

        if not message.recipients:
            raise RuntimeError("The email needs at least one recipient.")

        mime_message = MimeEmailMessage()
        mime_message["From"] = sender
        mime_message["To"] = ", ".join(message.recipients)
        mime_message["Subject"] = message.subject or ""

        plain_text = message.body or (
            "This email contains HTML content. "
            "Please open it in an HTML-capable email app."
        )
        mime_message.set_content(plain_text)

        if message.html:
            mime_message.add_alternative(message.html, subtype="html")

        raw_message = base64.urlsafe_b64encode(
            mime_message.as_bytes()
        ).decode("ascii").rstrip("=")

        access_token = self._get_access_token()

        request_body = json.dumps({"raw": raw_message}).encode("utf-8")
        request = urllib.request.Request(
            GMAIL_SEND_URL,
            data=request_body,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                response.read()
        except urllib.error.HTTPError as error:
            current_app.logger.error(
                "Gmail API send failed with HTTP status %s.",
                error.code,
            )
            raise RuntimeError(
                f"Gmail API could not send the email (HTTP {error.code})."
            ) from None
        except (urllib.error.URLError, TimeoutError) as error:
            current_app.logger.error(
                "Gmail API send failed: %s.",
                type(error).__name__,
            )
            raise RuntimeError(
                "Gmail API could not be reached to send the email."
            ) from None

    def _get_access_token(self):
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        token_file = Path(
            os.getenv(
                "GMAIL_TOKEN_FILE",
                str(Path.home() / ".collectix_gmail_token.json"),
            )
        ).expanduser()

        if not client_id or not client_secret:
            raise RuntimeError(
                "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
            )

        try:
            token_data = json.loads(token_file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise RuntimeError(
                "The Gmail refresh-token file is missing. "
                "Reconnect the sender account."
            ) from None
        except (OSError, json.JSONDecodeError):
            raise RuntimeError(
                "The Gmail refresh-token file could not be read."
            ) from None

        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            raise RuntimeError(
                "The Gmail refresh-token file has no refresh token."
            )

        form_data = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }).encode("utf-8")

        request = urllib.request.Request(
            GOOGLE_TOKEN_URL,
            data=form_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                response_data = json.loads(
                    response.read().decode("utf-8")
                )
        except urllib.error.HTTPError as error:
            current_app.logger.error(
                "Google token refresh failed with HTTP status %s.",
                error.code,
            )
            raise RuntimeError(
                "Google rejected the Gmail refresh token. "
                "Reconnect the sender account if the token expired."
            ) from None
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
        ) as error:
            current_app.logger.error(
                "Google token refresh failed: %s.",
                type(error).__name__,
            )
            raise RuntimeError(
                "Could not obtain a Gmail access token from Google."
            ) from None

        access_token = response_data.get("access_token")
        if not access_token:
            raise RuntimeError(
                "Google did not return a Gmail access token."
            )

        return access_token


mail = GmailMailer()