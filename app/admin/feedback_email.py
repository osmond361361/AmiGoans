from flask import current_app, render_template
from flask_mail import Message

from app.extensions import mail

SUBJECTS = {
    "idea": "Ami Goans responded to your idea",
    "issue": "Ami Goans responded to your issue report",
}


def send_feedback_response_email(feedback):
    message = Message(
        subject=SUBJECTS.get(feedback.kind, "Ami Goans responded to your feedback"),
        recipients=[feedback.submitted_by.email],
        body=render_template("email/feedback_response.txt", feedback=feedback),
        html=render_template("email/feedback_response.html", feedback=feedback),
    )
    try:
        mail.send(message)
    except Exception:
        current_app.logger.exception(
            "Failed to send feedback response email to %s", feedback.submitted_by.email
        )
        raise
