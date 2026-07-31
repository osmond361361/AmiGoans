import io

from PIL import Image

from app.extensions import db
from app.models import User
from app.models.photo import Photo


def _make_user(app, email, *, is_admin=False):
    with app.app_context():
        user = User(email=email, display_name="Test User", is_admin=is_admin)
        user.set_password("correcthorse123")
        db.session.add(user)
        db.session.commit()
        return user.id


def _sign_in(client, email):
    return client.post(
        "/auth/sign-in",
        data={"email": email, "password": "correcthorse123"},
        follow_redirects=True,
    )


def _test_image():
    buffer = io.BytesIO()
    Image.new("RGB", (400, 300), color="blue").save(buffer, "JPEG")
    buffer.seek(0)
    return buffer


def _submission_payload(**overrides):
    payload = {
        "caption": "Family picnic, 1985",
        "image": (_test_image(), "photo.jpg"),
    }
    payload.update(overrides)
    return payload


def test_submitting_a_photo_creates_a_pending_entry(client, app):
    _make_user(app, "member@example.com")
    _sign_in(client, "member@example.com")

    response = client.post(
        "/heritage/photos/add",
        data=_submission_payload(),
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        photo = Photo.query.filter_by(caption="Family picnic, 1985").first()
        assert photo is not None
        assert photo.status == "pending"
        assert photo.image


def test_submitting_a_photo_without_an_image_fails(client, app):
    _make_user(app, "member2@example.com")
    _sign_in(client, "member2@example.com")

    response = client.post(
        "/heritage/photos/add",
        data={"caption": "No photo attached"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200

    with app.app_context():
        assert Photo.query.filter_by(caption="No photo attached").first() is None


def test_pending_photo_does_not_appear_on_heritage_page(client, app):
    _make_user(app, "member3@example.com")
    _sign_in(client, "member3@example.com")
    client.post(
        "/heritage/photos/add", data=_submission_payload(), content_type="multipart/form-data"
    )
    client.get("/auth/sign-out")

    response = client.get("/heritage/")
    assert b"Family picnic, 1985" not in response.data


def test_admin_can_approve_a_photo_and_it_appears_on_heritage_page(client, app):
    _make_user(app, "member4@example.com", is_admin=False)
    _make_user(app, "admin@example.com", is_admin=True)
    _sign_in(client, "member4@example.com")
    client.post(
        "/heritage/photos/add", data=_submission_payload(), content_type="multipart/form-data"
    )
    client.get("/auth/sign-out")

    with app.app_context():
        photo_id = Photo.query.filter_by(caption="Family picnic, 1985").first().id

    _sign_in(client, "admin@example.com")
    response = client.post(
        f"/admin/photos/{photo_id}/status",
        data={"status": "approved", "return_status": "pending"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(Photo, photo_id).status == "approved"

    client.get("/auth/sign-out")
    response = client.get("/heritage/")
    assert b"Family picnic, 1985" in response.data


def test_non_author_cannot_edit_someone_elses_photo(client, app):
    _make_user(app, "member5@example.com")
    _make_user(app, "stranger@example.com")
    _sign_in(client, "member5@example.com")
    client.post(
        "/heritage/photos/add", data=_submission_payload(), content_type="multipart/form-data"
    )
    client.get("/auth/sign-out")

    with app.app_context():
        photo_id = Photo.query.filter_by(caption="Family picnic, 1985").first().id

    _sign_in(client, "stranger@example.com")
    response = client.get(f"/heritage/photos/{photo_id}/edit")
    assert response.status_code == 403


def test_non_admin_cannot_change_photo_status(client, app):
    _make_user(app, "member6@example.com")
    _sign_in(client, "member6@example.com")
    client.post(
        "/heritage/photos/add", data=_submission_payload(), content_type="multipart/form-data"
    )

    with app.app_context():
        photo_id = Photo.query.filter_by(caption="Family picnic, 1985").first().id

    response = client.post(
        f"/admin/photos/{photo_id}/status",
        data={"status": "approved", "return_status": "pending"},
    )
    assert response.status_code == 403
