import re

from app.auth.tokens import generate_reset_token, verify_reset_token
from app.extensions import db, mail
from app.models import User


def _make_user(app, email, password="correcthorse123"):
    with app.app_context():
        user = User(email=email, display_name="Reset Test User")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def test_forgot_password_sends_an_email_for_a_real_account(client, app):
    _make_user(app, "hasaccount@example.com")

    with mail.record_messages() as outbox:
        response = client.post(
            "/auth/forgot-password", data={"email": "hasaccount@example.com"}, follow_redirects=True
        )

    assert response.status_code == 200
    assert len(outbox) == 1
    assert outbox[0].recipients == ["hasaccount@example.com"]
    assert "reset-password" in outbox[0].html


def test_forgot_password_shows_the_same_message_for_an_unknown_email(client):
    with mail.record_messages() as outbox:
        response = client.post(
            "/auth/forgot-password", data={"email": "nobody@example.com"}, follow_redirects=True
        )

    assert response.status_code == 200
    assert len(outbox) == 0
    assert b"password reset link" in response.data


def test_reset_link_from_the_email_actually_resets_the_password(client, app):
    _make_user(app, "reset-me@example.com", password="oldpassword123")

    with mail.record_messages() as outbox:
        client.post("/auth/forgot-password", data={"email": "reset-me@example.com"})

    token = re.search(r"/auth/reset-password/([^\s\"<]+)", outbox[0].html).group(1)

    response = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword456", "confirm_password": "newpassword456"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email="reset-me@example.com").first()
        assert user.check_password("newpassword456")
        assert not user.check_password("oldpassword123")


def test_reset_token_cannot_be_reused_after_the_password_changes(client, app):
    with app.app_context():
        user = User(email="onetime@example.com", display_name="One Time")
        user.set_password("firstpassword1")
        db.session.add(user)
        db.session.commit()
        token = generate_reset_token(user)

    client.post(
        f"/auth/reset-password/{token}",
        data={"password": "secondpassword2", "confirm_password": "secondpassword2"},
    )

    # Reusing the same link a second time must fail, since the hash it was
    # issued against no longer matches.
    with app.app_context():
        user = User.query.filter_by(email="onetime@example.com").first()
        assert verify_reset_token(token) is None
        assert user.check_password("secondpassword2")


def test_expired_or_tampered_token_is_rejected(client, app):
    response = client.get("/auth/reset-password/not-a-real-token", follow_redirects=True)
    assert response.status_code == 200
    assert b"invalid or has expired" in response.data


def test_oauth_only_account_does_not_receive_a_reset_email(client, app):
    with app.app_context():
        user = User(
            email="oauth-only@example.com",
            display_name="OAuth Only",
            oauth_provider="google",
            oauth_id="12345",
        )
        db.session.add(user)
        db.session.commit()

    with mail.record_messages() as outbox:
        client.post("/auth/forgot-password", data={"email": "oauth-only@example.com"})

    assert len(outbox) == 0
