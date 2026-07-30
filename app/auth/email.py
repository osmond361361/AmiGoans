from flask import current_app, render_template, url_for
from flask_mail import Message

from app.extensions import mail


def send_password_reset_email(user, token):
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    message = Message(
        subject="Reset your Ami Goans password",
        recipients=[user.email],
        body=render_template("email/reset_password.txt", user=user, reset_url=reset_url),
        html=render_template("email/reset_password.html", user=user, reset_url=reset_url),
    )
    try:
        mail.send(message)
    except Exception:
        current_app.logger.exception("Failed to send password reset email to %s", user.email)
        raise
