import io

from PIL import Image

from app.models import User


def _make_test_image():
    buffer = io.BytesIO()
    Image.new("RGB", (200, 100), color="red").save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def _sign_up(client, email="member@example.com"):
    client.post(
        "/auth/join",
        data={
            "display_name": "Member Person",
            "email": email,
            "password": "correcthorse123",
            "confirm_password": "correcthorse123",
        },
    )


def test_profile_requires_login(client):
    response = client.get("/members/profile")
    assert response.status_code == 302
    assert "/auth/sign-in" in response.headers["Location"]


def test_profile_update_name_phone_and_consent(client, app):
    _sign_up(client)

    response = client.post(
        "/members/profile",
        data={
            "display_name": "Updated Name",
            "phone_number": "07700 900123",
            "sms_marketing_consent": "y",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email="member@example.com").first()
        assert user.display_name == "Updated Name"
        assert user.phone_number == "07700 900123"
        assert user.sms_marketing_consent is True
        assert user.sms_consent_at is not None


def test_profile_rejects_invalid_phone_number(client):
    _sign_up(client)

    response = client.post(
        "/members/profile",
        data={"display_name": "Member Person", "phone_number": "not-a-phone!!"},
    )
    assert response.status_code == 200
    assert b"valid phone number" in response.data


def test_profile_photo_upload_sets_avatar(client, app):
    _sign_up(client)

    response = client.post(
        "/members/profile",
        data={
            "display_name": "Member Person",
            "photo": (_make_test_image(), "avatar.png"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email="member@example.com").first()
        assert user.profile_photo is not None
