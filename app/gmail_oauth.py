import hmac
import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from flask import Blueprint, abort, current_app, redirect, request, session


gmail_oauth = Blueprint("gmail_oauth", __name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"


def _get_settings():
    settings = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "setup_key": os.getenv("GMAIL_OAUTH_SETUP_KEY"),
        "token_file": Path(
            os.getenv(
                "GMAIL_TOKEN_FILE",
                str(Path.home() / ".collectix_gmail_token.json"),
            )
        ).expanduser(),
    }

    required = ("client_id", "client_secret", "redirect_uri", "setup_key")
    if any(not settings[name] for name in required):
        raise RuntimeError("Gmail OAuth settings are missing from the environment.")

    return settings


@gmail_oauth.route("/gmail/oauth/setup", methods=["GET", "POST"])
def start_gmail_oauth():
    settings = _get_settings()

    # The setup page becomes unavailable after the token is saved.
    if settings["token_file"].exists():
        abort(404)

    if request.method == "GET":
        return """
        <!doctype html>
        <html lang="en">
          <head><meta charset="utf-8"><title>Connect CollectiX email</title></head>
          <body>
            <h1>Connect the CollectiX sender Gmail account</h1>
            <form method="post">
              <label for="setup_key">One-time setup key</label>
              <input id="setup_key" name="setup_key" type="password"
                     required autocomplete="current-password">
              <button type="submit">Continue to Google</button>
            </form>
          </body>
        </html>
        """

    submitted_key = request.form.get("setup_key", "")
    if not hmac.compare_digest(submitted_key, settings["setup_key"]):
        abort(403)

    state = secrets.token_urlsafe(32)
    session["gmail_oauth_state"] = state

    parameters = {
        "client_id": settings["client_id"],
        "redirect_uri": settings["redirect_uri"],
        "response_type": "code",
        "scope": GMAIL_SEND_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    authorization_url = (
        f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(parameters)}"
    )
    return redirect(authorization_url)


@gmail_oauth.route("/gmail/oauth/callback", methods=["GET"])
def gmail_oauth_callback():
    settings = _get_settings()

    expected_state = session.pop("gmail_oauth_state", None)
    received_state = request.args.get("state", "")

    if (
        not expected_state
        or not received_state
        or not secrets.compare_digest(expected_state, received_state)
    ):
        abort(400, "OAuth state check failed. Restart the connection process.")

    if request.args.get("error"):
        return "Google authorization was cancelled or denied.", 400

    authorization_code = request.args.get("code")
    if not authorization_code:
        abort(400, "Google did not return an authorization code.")

    form_data = urllib.parse.urlencode({
        "code": authorization_code,
        "client_id": settings["client_id"],
        "client_secret": settings["client_secret"],
        "redirect_uri": settings["redirect_uri"],
        "grant_type": "authorization_code",
    }).encode("utf-8")

    token_request = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(token_request, timeout=20) as response:
            token_data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        current_app.logger.error(
            "Gmail OAuth token exchange failed: %s",
            type(error).__name__,
        )
        return "Google token exchange failed. Check the server error log.", 502

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        return (
            "Google did not return a refresh token. "
            "Restart authorization and approve the requested permission.",
            400,
        )

    token_file = settings["token_file"]
    token_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    file_descriptor = os.open(
        token_file,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        0o600,
    )
    with os.fdopen(file_descriptor, "w", encoding="utf-8") as token_output:
        json.dump({"refresh_token": refresh_token}, token_output)

    os.chmod(token_file, 0o600)

    return (
        "CollectiX is connected to the sender Gmail account. "
        "The token was saved privately on the server."
    )