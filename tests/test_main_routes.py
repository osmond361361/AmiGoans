import pytest


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Bringing Goans" in response.data


@pytest.mark.parametrize(
    "path",
    [
        "/about",
        "/motto",
        "/contact",
        "/legal",
        "/auth/sign-in",
        "/auth/join",
        "/members/",
        "/businesses/",
        "/events/",
        "/heritage/",
        "/heritage/blogs",
        "/heritage/cuisine",
        "/tv/",
        "/jobs/",
        "/admin/",
    ],
)
def test_nav_pages_load(client, path):
    response = client.get(path)
    assert response.status_code == 200


def test_404_page(client):
    response = client.get("/this-page-does-not-exist")
    assert response.status_code == 404
    assert b"Page Not Found" in response.data


@pytest.mark.parametrize("path", ["/businesses/add", "/jobs/add"])
def test_add_routes_require_login(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert "/auth/sign-in" in response.headers["Location"]
