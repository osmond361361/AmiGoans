from app.extensions import db
from app.models import User
from app.models.story import Story


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
        "title": "Growing Up in Goa",
        "body": "A" * 60,
    }
    payload.update(overrides)
    return payload


def test_submitting_a_story_creates_a_pending_listing(client, app):
    _make_user(app, "author@example.com")
    _sign_in(client, "author@example.com")

    response = client.post(
        "/heritage/stories/add", data=_submission_payload(), follow_redirects=True
    )
    assert response.status_code == 200

    with app.app_context():
        story = Story.query.filter_by(title="Growing Up in Goa").first()
        assert story is not None
        assert story.status == "pending"
        assert story.slug == "growing-up-in-goa"


def test_pending_story_does_not_appear_in_public_listing(client, app):
    _make_user(app, "author2@example.com")
    _sign_in(client, "author2@example.com")
    client.post("/heritage/stories/add", data=_submission_payload())
    client.get("/auth/sign-out")

    response = client.get("/heritage/blogs")
    assert b"Growing Up in Goa" not in response.data


def test_pending_story_detail_is_hidden_from_the_public(client, app):
    _make_user(app, "author3@example.com")
    _sign_in(client, "author3@example.com")
    client.post("/heritage/stories/add", data=_submission_payload())
    client.get("/auth/sign-out")

    response = client.get("/heritage/stories/growing-up-in-goa")
    assert response.status_code == 404


def test_admin_can_approve_a_story_and_it_shows_the_author(client, app):
    _make_user(app, "author4@example.com", is_admin=False)
    _make_user(app, "admin@example.com", is_admin=True)
    _sign_in(client, "author4@example.com")
    client.post("/heritage/stories/add", data=_submission_payload())
    client.get("/auth/sign-out")

    with app.app_context():
        story_id = Story.query.filter_by(title="Growing Up in Goa").first().id

    _sign_in(client, "admin@example.com")
    response = client.post(
        f"/admin/stories/{story_id}/status",
        data={"status": "approved", "return_status": "pending"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(Story, story_id).status == "approved"

    client.get("/auth/sign-out")
    listing_response = client.get("/heritage/blogs")
    assert b"Growing Up in Goa" in listing_response.data

    detail_response = client.get("/heritage/stories/growing-up-in-goa")
    assert b"Test User" in detail_response.data


def test_non_author_cannot_edit_someone_elses_story(client, app):
    _make_user(app, "author5@example.com")
    _make_user(app, "stranger@example.com")
    _sign_in(client, "author5@example.com")
    client.post("/heritage/stories/add", data=_submission_payload())
    client.get("/auth/sign-out")

    _sign_in(client, "stranger@example.com")
    response = client.get("/heritage/stories/growing-up-in-goa/edit")
    assert response.status_code == 403


def test_non_admin_cannot_change_story_status(client, app):
    _make_user(app, "author6@example.com")
    _sign_in(client, "author6@example.com")
    client.post("/heritage/stories/add", data=_submission_payload())

    with app.app_context():
        story_id = Story.query.filter_by(title="Growing Up in Goa").first().id

    response = client.post(
        f"/admin/stories/{story_id}/status",
        data={"status": "approved", "return_status": "pending"},
    )
    assert response.status_code == 403
