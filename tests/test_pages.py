from app.extensions import db
from app.models import Page, User


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


def _seed_pages(app):
    with app.app_context():
        db.session.add_all(
            [
                Page(slug="motto", title="Our Motto", content_html="<p>Together we rise.</p>"),
                Page(slug="about", title="About Ami Goans", content_html="<p>Who we are.</p>"),
                Page(slug="contact", title="Contact Us", content_html="<p>Reach out.</p>"),
                Page(
                    slug="privacy-policy",
                    title="Privacy Policy",
                    content_html="<p>How we handle data.</p>",
                ),
                Page(
                    slug="terms-conditions",
                    title="Terms & Conditions",
                    content_html="<p>The rules.</p>",
                ),
                Page(
                    slug="community-guidelines",
                    title="Community Guidelines",
                    content_html="<p>Be kind.</p>",
                ),
            ]
        )
        db.session.commit()


def test_about_page_renders_content_from_database(client, app):
    _seed_pages(app)

    response = client.get("/about")
    assert response.status_code == 200
    assert b"About Ami Goans" in response.data
    assert b"Who we are." in response.data


def test_legal_page_renders_privacy_terms_and_guidelines(client, app):
    _seed_pages(app)

    response = client.get("/legal")
    assert response.status_code == 200
    assert b"Privacy Policy" in response.data
    assert b"Terms &amp; Conditions" in response.data
    assert b"Community Guidelines" in response.data


def test_admin_pages_list_requires_login(client):
    response = client.get("/admin/pages")
    assert response.status_code == 302
    assert "/auth/sign-in" in response.headers["Location"]


def test_admin_pages_list_rejects_non_admin_member(client, app):
    _make_user(app, "member@example.com", is_admin=False)
    _sign_in(client, "member@example.com")

    response = client.get("/admin/pages")
    assert response.status_code == 403


def test_admin_pages_list_shows_all_pages_for_admin(client, app):
    _seed_pages(app)
    _make_user(app, "admin@example.com", is_admin=True)
    _sign_in(client, "admin@example.com")

    response = client.get("/admin/pages")
    assert response.status_code == 200
    assert b"Manage Pages" in response.data
    assert b"Our Motto" in response.data


def test_edit_page_requires_admin(client, app):
    _seed_pages(app)
    _make_user(app, "member2@example.com", is_admin=False)
    _sign_in(client, "member2@example.com")

    response = client.get("/admin/pages/motto/edit")
    assert response.status_code == 403


def test_edit_page_unknown_slug_returns_404(client, app):
    _make_user(app, "admin2@example.com", is_admin=True)
    _sign_in(client, "admin2@example.com")

    response = client.get("/admin/pages/not-a-real-page/edit")
    assert response.status_code == 404


def test_admin_can_update_a_page_and_it_appears_on_public_site(client, app):
    _seed_pages(app)
    _make_user(app, "admin3@example.com", is_admin=True)
    _sign_in(client, "admin3@example.com")

    response = client.post(
        "/admin/pages/motto/edit",
        data={"title": "Our New Motto", "content_html": "<p>Together we rise.</p>"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"has been updated" in response.data

    public_response = client.get("/motto")
    assert b"Our New Motto" in public_response.data
    assert b"Together we rise." in public_response.data
