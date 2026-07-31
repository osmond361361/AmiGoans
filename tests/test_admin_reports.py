from unittest.mock import patch

from app.extensions import db
from app.models import User


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


def test_reports_page_requires_login(client):
    response = client.get("/admin/reports")
    assert response.status_code == 302
    assert "/auth/sign-in" in response.headers["Location"]


def test_reports_page_rejects_non_admin_member(client, app):
    _make_user(app, "member@example.com", is_admin=False)
    _sign_in(client, "member@example.com")

    response = client.get("/admin/reports")
    assert response.status_code == 403


def test_reports_page_shows_counts_but_not_a_user_table(client, app):
    _make_user(app, "admin@example.com", is_admin=True)
    _sign_in(client, "admin@example.com")

    response = client.get("/admin/reports")
    assert response.status_code == 200
    assert b"Registered users" in response.data
    assert b"admin@example.com" not in response.data


def test_users_csv_download_contains_registered_users(client, app):
    _make_user(app, "member2@example.com", is_admin=False)
    _make_user(app, "admin2@example.com", is_admin=True)
    _sign_in(client, "admin2@example.com")

    response = client.get("/admin/reports/users.csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert b"member2@example.com" in response.data
    assert b"admin2@example.com" in response.data


def test_hits_csv_download_for_a_private_ip_needs_no_network_call(client, app):
    _make_user(app, "admin3@example.com", is_admin=True)
    client.get("/", environ_overrides={"REMOTE_ADDR": "127.0.0.1"})
    _sign_in(client, "admin3@example.com")

    response = client.get("/admin/reports/hits.csv")
    assert response.status_code == 200
    assert b"127.0.0.1" in response.data


@patch("app.admin.geolocation.requests.get")
def test_hits_csv_download_resolves_location_for_a_public_ip(mock_get, client, app):
    mock_get.return_value.json.return_value = {
        "status": "success",
        "city": "Manchester",
        "regionName": "England",
        "country": "United Kingdom",
    }

    _make_user(app, "admin4@example.com", is_admin=True)
    client.get("/", environ_overrides={"REMOTE_ADDR": "8.8.8.8"})
    _sign_in(client, "admin4@example.com")

    response = client.get("/admin/reports/hits.csv")
    assert response.status_code == 200
    assert b"8.8.8.8" in response.data
    assert b"Manchester" in response.data
    assert b"United Kingdom" in response.data


def test_users_csv_respects_date_range_filter(client, app):
    _make_user(app, "admin5@example.com", is_admin=True)
    _sign_in(client, "admin5@example.com")

    response = client.get("/admin/reports/users.csv?start=2999-01-01&end=2999-01-02")
    assert response.status_code == 200
    assert b"admin5@example.com" not in response.data
