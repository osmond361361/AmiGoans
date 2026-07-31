import re

from app.extensions import db
from app.models import Business, User


def _extract_csrf_token(html):
    match = re.search(rb'name="csrf_token" value="([^"]+)"', html)
    assert match is not None, "no csrf_token field found in the response"
    return match.group(1).decode()


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


def _submission_payload(**overrides):
    payload = {
        "name": "Example Goan Kitchen",
        "description": "A wonderful Goan restaurant serving fish curry and vindaloo.",
        "category": "Restaurants",
        "town": "Manchester",
        "county": "Greater Manchester",
        "nation": "England",
        "telephone": "",
        "whatsapp": "",
        "email": "",
        "website": "",
        "facebook_url": "",
        "postcode_district": "",
    }
    payload.update(overrides)
    return payload


def test_submitting_a_business_creates_a_pending_listing(client, app):
    _make_user(app, "owner@example.com")
    _sign_in(client, "owner@example.com")

    response = client.post("/businesses/add", data=_submission_payload(), follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        business = Business.query.filter_by(name="Example Goan Kitchen").first()
        assert business is not None
        assert business.status == "pending"
        assert business.slug == "example-goan-kitchen"


def test_pending_business_does_not_appear_in_public_directory(client, app):
    _make_user(app, "owner2@example.com")
    _sign_in(client, "owner2@example.com")
    client.post("/businesses/add", data=_submission_payload())
    client.get("/auth/sign-out")

    response = client.get("/businesses/")
    assert b"Example Goan Kitchen" not in response.data


def test_pending_business_detail_is_hidden_from_the_public(client, app):
    _make_user(app, "owner3@example.com")
    _sign_in(client, "owner3@example.com")
    client.post("/businesses/add", data=_submission_payload())
    client.get("/auth/sign-out")

    response = client.get("/businesses/example-goan-kitchen")
    assert response.status_code == 404


def test_owner_can_see_their_own_pending_listing(client, app):
    _make_user(app, "owner4@example.com")
    _sign_in(client, "owner4@example.com")
    client.post("/businesses/add", data=_submission_payload())

    response = client.get("/businesses/example-goan-kitchen")
    assert response.status_code == 200


def test_admin_can_approve_a_business_and_it_becomes_public(client, app):
    _make_user(app, "owner5@example.com")
    _make_user(app, "admin@example.com", is_admin=True)
    _sign_in(client, "owner5@example.com")
    client.post("/businesses/add", data=_submission_payload())
    client.get("/auth/sign-out")

    with app.app_context():
        business_id = Business.query.filter_by(name="Example Goan Kitchen").first().id

    _sign_in(client, "admin@example.com")
    response = client.post(
        f"/admin/businesses/{business_id}/status",
        data={"status": "approved", "return_status": "pending"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(Business, business_id).status == "approved"

    client.get("/auth/sign-out")
    directory_response = client.get("/businesses/")
    assert b"Example Goan Kitchen" in directory_response.data


def test_non_owner_cannot_edit_someone_elses_business(client, app):
    _make_user(app, "owner6@example.com")
    _make_user(app, "stranger@example.com")
    _sign_in(client, "owner6@example.com")
    client.post("/businesses/add", data=_submission_payload())
    client.get("/auth/sign-out")

    _sign_in(client, "stranger@example.com")
    response = client.get("/businesses/example-goan-kitchen/edit")
    assert response.status_code == 403


def test_directory_search_filters_by_category(client, app):
    _make_user(app, "owner7@example.com")
    _make_user(app, "admin7@example.com", is_admin=True)
    _sign_in(client, "owner7@example.com")
    client.post("/businesses/add", data=_submission_payload(name="Ocean Travel", category="Travel"))
    client.get("/auth/sign-out")

    with app.app_context():
        business = Business.query.filter_by(name="Ocean Travel").first()
        business.status = "approved"
        db.session.commit()

    response = client.get("/businesses/?category=Travel")
    assert b"Ocean Travel" in response.data

    response = client.get("/businesses/?category=Restaurants")
    assert b"Ocean Travel" not in response.data


def test_non_admin_cannot_change_business_status(client, app):
    _make_user(app, "owner8@example.com")
    _sign_in(client, "owner8@example.com")
    client.post("/businesses/add", data=_submission_payload())

    with app.app_context():
        business_id = Business.query.filter_by(name="Example Goan Kitchen").first().id

    response = client.post(
        f"/admin/businesses/{business_id}/status",
        data={"status": "approved", "return_status": "pending"},
    )
    assert response.status_code == 403


def test_business_status_update_form_carries_a_valid_csrf_token(client, app):
    _make_user(app, "owner9@example.com")
    _make_user(app, "admin9@example.com", is_admin=True)
    _sign_in(client, "owner9@example.com")
    client.post("/businesses/add", data=_submission_payload(name="CSRF Regression Kitchen"))
    client.get("/auth/sign-out")

    _sign_in(client, "admin9@example.com")

    with app.app_context():
        business_id = Business.query.filter_by(name="CSRF Regression Kitchen").first().id

    app.config["WTF_CSRF_ENABLED"] = True
    try:
        page = client.get("/admin/businesses")
        token = _extract_csrf_token(page.data)

        response = client.post(
            f"/admin/businesses/{business_id}/status",
            data={"status": "approved", "return_status": "pending", "csrf_token": token},
        )
        assert response.status_code == 302
    finally:
        app.config["WTF_CSRF_ENABLED"] = False
