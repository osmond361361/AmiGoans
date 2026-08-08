import io

from PIL import Image

from app.extensions import db
from app.models import User
from app.models.village import Village
from app.models.village_landmark import VillageLandmark
from app.models.village_photo import VillagePhoto


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


def _make_village(app, **overrides):
    with app.app_context():
        defaults = {
            "name": "Aldona",
            "slug": "aldona-bardez",
            "taluka": "Bardez",
            "district": "North Goa",
            "gram_panchayat": "Aldona",
            "category": "Rural",
        }
        defaults.update(overrides)
        village = Village(**defaults)
        db.session.add(village)
        db.session.commit()
        return village.id


def _test_image():
    buffer = io.BytesIO()
    Image.new("RGB", (400, 300), color="green").save(buffer, "JPEG")
    buffer.seek(0)
    return buffer


def test_index_page_lists_villages(client, app):
    _make_village(app)
    response = client.get("/villages/")
    assert response.status_code == 200
    assert b"Aldona" in response.data
    assert b"Bardez" in response.data


def test_detail_page_shows_village_facts(client, app):
    _make_village(app)
    response = client.get("/villages/aldona-bardez")
    assert response.status_code == 200
    assert b"Aldona" in response.data
    assert b"North Goa" in response.data


def test_detail_page_404s_for_unknown_slug(client, app):
    response = client.get("/villages/does-not-exist")
    assert response.status_code == 404


def test_submitting_a_landmark_creates_a_pending_entry(client, app):
    _make_village(app)
    _make_user(app, "member@example.com")
    _sign_in(client, "member@example.com")

    response = client.post(
        "/villages/aldona-bardez/landmarks/add",
        data={
            "category": "church",
            "name": "St. Thomas Church",
            "description": "Old parish church.",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        landmark = VillageLandmark.query.filter_by(name="St. Thomas Church").first()
        assert landmark is not None
        assert landmark.status == "pending"


def test_pending_landmark_not_shown_on_detail_page(client, app):
    _make_village(app)
    _make_user(app, "member2@example.com")
    _sign_in(client, "member2@example.com")
    client.post(
        "/villages/aldona-bardez/landmarks/add",
        data={"category": "church", "name": "St. Thomas Church", "description": ""},
    )

    response = client.get("/villages/aldona-bardez")
    assert b"St. Thomas Church" not in response.data


def test_admin_can_approve_a_landmark_and_it_appears_on_detail_page(client, app):
    _make_village(app)
    _make_user(app, "member3@example.com")
    _make_user(app, "admin@example.com", is_admin=True)
    _sign_in(client, "member3@example.com")
    client.post(
        "/villages/aldona-bardez/landmarks/add",
        data={"category": "temple", "name": "Shanti Durga Temple", "description": ""},
    )
    client.get("/auth/sign-out")

    with app.app_context():
        landmark_id = VillageLandmark.query.filter_by(name="Shanti Durga Temple").first().id

    _sign_in(client, "admin@example.com")
    response = client.post(
        f"/admin/villages/landmarks/{landmark_id}/status",
        data={"status": "approved", "return_status": "pending"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    client.get("/auth/sign-out")
    response = client.get("/villages/aldona-bardez")
    assert b"Shanti Durga Temple" in response.data


def test_non_admin_cannot_change_landmark_status(client, app):
    _make_village(app)
    _make_user(app, "member4@example.com")
    _sign_in(client, "member4@example.com")
    client.post(
        "/villages/aldona-bardez/landmarks/add",
        data={"category": "school", "name": "Government Primary School", "description": ""},
    )

    with app.app_context():
        landmark_id = VillageLandmark.query.filter_by(name="Government Primary School").first().id

    response = client.post(
        f"/admin/villages/landmarks/{landmark_id}/status",
        data={"status": "approved", "return_status": "pending"},
    )
    assert response.status_code == 403


def test_submitting_a_village_photo_creates_a_pending_entry(client, app):
    _make_village(app)
    _make_user(app, "member5@example.com")
    _sign_in(client, "member5@example.com")

    response = client.post(
        "/villages/aldona-bardez/photos/add",
        data={"caption": "Village square", "image": (_test_image(), "photo.jpg")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        photo = VillagePhoto.query.filter_by(caption="Village square").first()
        assert photo is not None
        assert photo.status == "pending"


def test_pending_village_photo_not_shown_on_detail_page(client, app):
    _make_village(app)
    _make_user(app, "member6@example.com")
    _sign_in(client, "member6@example.com")
    client.post(
        "/villages/aldona-bardez/photos/add",
        data={"caption": "Village square", "image": (_test_image(), "photo.jpg")},
        content_type="multipart/form-data",
    )

    response = client.get("/villages/aldona-bardez")
    assert b"Village square" not in response.data


def test_admin_can_approve_a_village_photo_and_it_appears_on_detail_page(client, app):
    _make_village(app)
    _make_user(app, "member7@example.com")
    _make_user(app, "admin2@example.com", is_admin=True)
    _sign_in(client, "member7@example.com")
    client.post(
        "/villages/aldona-bardez/photos/add",
        data={"caption": "Village square", "image": (_test_image(), "photo.jpg")},
        content_type="multipart/form-data",
    )
    client.get("/auth/sign-out")

    with app.app_context():
        photo_id = VillagePhoto.query.filter_by(caption="Village square").first().id

    _sign_in(client, "admin2@example.com")
    response = client.post(
        f"/admin/villages/photos/{photo_id}/status",
        data={"status": "approved", "return_status": "pending"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    client.get("/auth/sign-out")
    response = client.get("/villages/aldona-bardez")
    assert b"Village square" in response.data


def test_non_admin_cannot_change_village_photo_status(client, app):
    _make_village(app)
    _make_user(app, "member8@example.com")
    _sign_in(client, "member8@example.com")
    client.post(
        "/villages/aldona-bardez/photos/add",
        data={"caption": "Village square", "image": (_test_image(), "photo.jpg")},
        content_type="multipart/form-data",
    )

    with app.app_context():
        photo_id = VillagePhoto.query.filter_by(caption="Village square").first().id

    response = client.post(
        f"/admin/villages/photos/{photo_id}/status",
        data={"status": "approved", "return_status": "pending"},
    )
    assert response.status_code == 403


def test_my_submissions_requires_login(client, app):
    response = client.get("/villages/mine")
    assert response.status_code == 302


def test_my_submissions_lists_users_own_submissions(client, app):
    _make_village(app)
    _make_user(app, "member9@example.com")
    _sign_in(client, "member9@example.com")
    client.post(
        "/villages/aldona-bardez/landmarks/add",
        data={"category": "other", "name": "Old Banyan Tree", "description": ""},
    )

    response = client.get("/villages/mine")
    assert response.status_code == 200
    assert b"Old Banyan Tree" in response.data


def test_detail_page_caches_wikipedia_info_on_first_view(client, app, monkeypatch):
    village_id = _make_village(app)
    calls = []

    def fake_fetch(name, **kwargs):
        calls.append(name)
        return {
            "wiki_summary": "Aldona is a village in Bardez taluka of Goa, India.",
            "wiki_history": "Aldona was historically known for its churches.",
            "wiki_url": "https://en.wikipedia.org/wiki/Aldona",
            "wiki_image": None,
            "wiki_image_attribution": None,
            "wiki_image_source_url": None,
        }

    monkeypatch.setattr("app.villages.routes.fetch_village_wikipedia", fake_fetch)

    response = client.get("/villages/aldona-bardez")
    assert response.status_code == 200
    assert b"Aldona is a village in Bardez taluka" in response.data
    assert b"Aldona was historically known for its churches" in response.data
    assert calls == ["Aldona"]

    with app.app_context():
        village = db.session.get(Village, village_id)
        assert village.wiki_summary == "Aldona is a village in Bardez taluka of Goa, India."
        assert village.wiki_checked_at is not None


def test_detail_page_does_not_refetch_once_already_checked(client, app, monkeypatch):
    from datetime import datetime, timezone

    _make_village(app)
    with app.app_context():
        village = Village.query.filter_by(slug="aldona-bardez").first()
        village.wiki_checked_at = datetime.now(timezone.utc)
        db.session.commit()

    def fail_if_called(*args, **kwargs):
        raise AssertionError("should not re-fetch a village already checked")

    monkeypatch.setattr("app.villages.routes.fetch_village_wikipedia", fail_if_called)

    response = client.get("/villages/aldona-bardez")
    assert response.status_code == 200


def test_detail_page_survives_a_wikipedia_lookup_error(client, app, monkeypatch):
    _make_village(app)

    def raise_error(*args, **kwargs):
        raise RuntimeError("network unreachable")

    monkeypatch.setattr("app.villages.routes.fetch_village_wikipedia", raise_error)

    response = client.get("/villages/aldona-bardez")
    assert response.status_code == 200


def test_admin_can_edit_village_population(client, app):
    village_id = _make_village(app)
    _make_user(app, "admin3@example.com", is_admin=True)
    _sign_in(client, "admin3@example.com")

    response = client.post(
        f"/admin/villages/{village_id}/edit",
        data={
            "gram_panchayat": "Aldona",
            "category": "Rural",
            "population": "8500",
            "population_source": "Community submission",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        village = db.session.get(Village, village_id)
        assert village.population == 8500
        assert village.population_source == "Community submission"
