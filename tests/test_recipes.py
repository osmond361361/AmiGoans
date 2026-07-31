from app.extensions import db
from app.models import User
from app.models.recipe import Recipe


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
        "title": "Grandma's Fish Curry",
        "ingredients": "Fish, coconut, kokum, chillies",
        "instructions": "Simmer everything together until cooked through.",
    }
    payload.update(overrides)
    return payload


def test_submitting_a_recipe_creates_a_pending_listing(client, app):
    _make_user(app, "cook@example.com")
    _sign_in(client, "cook@example.com")

    response = client.post(
        "/heritage/recipes/add", data=_submission_payload(), follow_redirects=True
    )
    assert response.status_code == 200

    with app.app_context():
        recipe = Recipe.query.filter_by(title="Grandma's Fish Curry").first()
        assert recipe is not None
        assert recipe.status == "pending"
        assert recipe.slug == "grandma-s-fish-curry"


def test_pending_recipe_does_not_appear_on_cuisine_page(client, app):
    _make_user(app, "cook2@example.com")
    _sign_in(client, "cook2@example.com")
    client.post("/heritage/recipes/add", data=_submission_payload())
    client.get("/auth/sign-out")

    response = client.get("/heritage/cuisine")
    assert b"Grandma&#39;s Fish Curry" not in response.data
    assert b"Grandma's Fish Curry" not in response.data


def test_admin_can_approve_a_recipe_and_it_appears_on_cuisine_page(client, app):
    _make_user(app, "cook3@example.com", is_admin=False)
    _make_user(app, "admin@example.com", is_admin=True)
    _sign_in(client, "cook3@example.com")
    client.post("/heritage/recipes/add", data=_submission_payload())
    client.get("/auth/sign-out")

    with app.app_context():
        recipe_id = Recipe.query.filter_by(title="Grandma's Fish Curry").first().id

    _sign_in(client, "admin@example.com")
    response = client.post(
        f"/admin/recipes/{recipe_id}/status",
        data={"status": "approved", "return_status": "pending"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(Recipe, recipe_id).status == "approved"

    client.get("/auth/sign-out")
    cuisine_response = client.get("/heritage/cuisine")
    assert b"Grandma&#39;s Fish Curry" in cuisine_response.data


def test_non_author_cannot_edit_someone_elses_recipe(client, app):
    _make_user(app, "cook4@example.com")
    _make_user(app, "stranger@example.com")
    _sign_in(client, "cook4@example.com")
    client.post("/heritage/recipes/add", data=_submission_payload())
    client.get("/auth/sign-out")

    _sign_in(client, "stranger@example.com")
    response = client.get("/heritage/recipes/grandma-s-fish-curry/edit")
    assert response.status_code == 403


def test_non_admin_cannot_change_recipe_status(client, app):
    _make_user(app, "cook5@example.com")
    _sign_in(client, "cook5@example.com")
    client.post("/heritage/recipes/add", data=_submission_payload())

    with app.app_context():
        recipe_id = Recipe.query.filter_by(title="Grandma's Fish Curry").first().id

    response = client.post(
        f"/admin/recipes/{recipe_id}/status",
        data={"status": "approved", "return_status": "pending"},
    )
    assert response.status_code == 403
