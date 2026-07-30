from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

RESET_PASSWORD_MAX_AGE = 3600  # 1 hour
RESET_PASSWORD_SALT = "reset-password"


def generate_reset_token(user):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(
        {"user_id": user.id, "hash": user.password_hash}, salt=RESET_PASSWORD_SALT
    )


def verify_reset_token(token):
    """Return the User the token was issued for, or None if it's invalid,
    expired, or the account's password has changed since it was issued.

    The token payload carries the password hash that was current when it
    was generated (not just the user id) -- resetting the password (or a
    second concurrent reset) changes the hash, which makes any
    previously-issued token fail this comparison automatically, without
    needing a separate "used" column to track single-use.
    """
    from app.models import User

    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        payload = serializer.loads(token, salt=RESET_PASSWORD_SALT, max_age=RESET_PASSWORD_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None

    user = User.query.get(payload.get("user_id"))
    if user is None or user.password_hash != payload.get("hash"):
        return None
    return user
