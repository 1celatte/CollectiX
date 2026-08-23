from . import auth


@auth.route("/test-auth")
def test_auth():
    return "Auth Blueprint is working!"