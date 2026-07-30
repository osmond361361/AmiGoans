from app.extensions import db
from app.models import SiteVisit, User


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


def test_visiting_a_page_records_a_site_visit(client, app):
    client.get("/", environ_overrides={"REMOTE_ADDR": "203.0.113.5"})

    with app.app_context():
        visit = SiteVisit.query.filter_by(ip_address="203.0.113.5").first()
        assert visit is not None
        assert visit.path == "/"


def test_static_files_are_not_logged(client, app):
    client.get("/static/css/style.css")

    with app.app_context():
        assert SiteVisit.query.filter_by(path="/static/css/style.css").count() == 0


def test_admin_dashboard_requires_login(client):
    response = client.get("/admin/")
    assert response.status_code == 302
    assert "/auth/sign-in" in response.headers["Location"]


def test_admin_dashboard_rejects_non_admin_member(client, app):
    _make_user(app, "member@example.com", is_admin=False)
    _sign_in(client, "member@example.com")

    response = client.get("/admin/")
    assert response.status_code == 403


def test_admin_dashboard_shows_hit_counts_for_admin(client, app):
    _make_user(app, "admin@example.com", is_admin=True)

    client.get("/businesses", environ_overrides={"REMOTE_ADDR": "198.51.100.9"})

    _sign_in(client, "admin@example.com")
    response = client.get("/admin/")

    assert response.status_code == 200
    assert b"198.51.100.9" in response.data
    assert b"Total hits" in response.data
