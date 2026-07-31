from app.extensions import db
from app.models import User
from app.models.job import JobPost


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
        "title": "Warehouse Operative",
        "location": "Manchester",
        "job_url": "https://example.com/careers/warehouse-operative",
        "description": "Full-time role, immediate start.",
    }
    payload.update(overrides)
    return payload


def test_submitting_a_job_creates_a_pending_listing(client, app):
    _make_user(app, "poster@example.com")
    _sign_in(client, "poster@example.com")

    response = client.post("/jobs/add", data=_submission_payload(), follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        job = JobPost.query.filter_by(title="Warehouse Operative").first()
        assert job is not None
        assert job.status == "pending"
        assert job.slug == "warehouse-operative"


def test_pending_job_does_not_appear_in_public_listing(client, app):
    _make_user(app, "poster2@example.com")
    _sign_in(client, "poster2@example.com")
    client.post("/jobs/add", data=_submission_payload())
    client.get("/auth/sign-out")

    response = client.get("/jobs/")
    assert b"Warehouse Operative" not in response.data


def test_pending_job_detail_is_hidden_from_the_public(client, app):
    _make_user(app, "poster3@example.com")
    _sign_in(client, "poster3@example.com")
    client.post("/jobs/add", data=_submission_payload())
    client.get("/auth/sign-out")

    response = client.get("/jobs/warehouse-operative")
    assert response.status_code == 404


def test_admin_can_approve_a_job_and_it_shows_the_poster(client, app):
    _make_user(app, "poster4@example.com", is_admin=False)
    _make_user(app, "admin@example.com", is_admin=True)
    _sign_in(client, "poster4@example.com")
    client.post("/jobs/add", data=_submission_payload())
    client.get("/auth/sign-out")

    with app.app_context():
        job_id = JobPost.query.filter_by(title="Warehouse Operative").first().id

    _sign_in(client, "admin@example.com")
    response = client.post(
        f"/admin/jobs/{job_id}/status",
        data={"status": "approved", "return_status": "pending"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(JobPost, job_id).status == "approved"

    client.get("/auth/sign-out")
    listing_response = client.get("/jobs/")
    assert b"Warehouse Operative" in listing_response.data

    detail_response = client.get("/jobs/warehouse-operative")
    assert b"Test User" in detail_response.data


def test_non_owner_cannot_edit_someone_elses_job(client, app):
    _make_user(app, "poster5@example.com")
    _make_user(app, "stranger@example.com")
    _sign_in(client, "poster5@example.com")
    client.post("/jobs/add", data=_submission_payload())
    client.get("/auth/sign-out")

    _sign_in(client, "stranger@example.com")
    response = client.get("/jobs/warehouse-operative/edit")
    assert response.status_code == 403


def test_non_admin_cannot_change_job_status(client, app):
    _make_user(app, "poster6@example.com")
    _sign_in(client, "poster6@example.com")
    client.post("/jobs/add", data=_submission_payload())

    with app.app_context():
        job_id = JobPost.query.filter_by(title="Warehouse Operative").first().id

    response = client.post(
        f"/admin/jobs/{job_id}/status",
        data={"status": "approved", "return_status": "pending"},
    )
    assert response.status_code == 403
