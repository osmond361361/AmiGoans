from app.models import User


def test_join_creates_user_and_logs_in(client, app):
    response = client.post(
        "/auth/join",
        data={
            "display_name": "Test User",
            "email": "test@example.com",
            "password": "correcthorse123",
            "confirm_password": "correcthorse123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        assert user is not None
        assert user.display_name == "Test User"
        assert user.check_password("correcthorse123")


def test_join_rejects_duplicate_email(client):
    payload = {
        "display_name": "Test User",
        "email": "dupe@example.com",
        "password": "correcthorse123",
        "confirm_password": "correcthorse123",
    }
    client.post("/auth/join", data=payload)
    client.get("/auth/sign-out")

    response = client.post("/auth/join", data=payload)
    assert b"already exists" in response.data


def test_join_rejects_mismatched_passwords(client):
    response = client.post(
        "/auth/join",
        data={
            "display_name": "Test User",
            "email": "mismatch@example.com",
            "password": "correcthorse123",
            "confirm_password": "somethingelse",
        },
    )
    assert response.status_code == 200
    with client.session_transaction() as session:
        assert "_user_id" not in session


def test_sign_in_with_correct_password(client):
    client.post(
        "/auth/join",
        data={
            "display_name": "Sign In Person",
            "email": "signin@example.com",
            "password": "correcthorse123",
            "confirm_password": "correcthorse123",
        },
    )
    client.get("/auth/sign-out")

    response = client.post(
        "/auth/sign-in",
        data={"email": "signin@example.com", "password": "correcthorse123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Welcome back" in response.data


def test_sign_in_with_wrong_password(client):
    client.post(
        "/auth/join",
        data={
            "display_name": "Wrong Password",
            "email": "wrongpw@example.com",
            "password": "correcthorse123",
            "confirm_password": "correcthorse123",
        },
    )
    client.get("/auth/sign-out")

    response = client.post(
        "/auth/sign-in",
        data={"email": "wrongpw@example.com", "password": "notthepassword"},
    )
    assert response.status_code == 200
    assert b"Incorrect email or password" in response.data


def test_sign_out_requires_login_then_clears_session(client):
    client.post(
        "/auth/join",
        data={
            "display_name": "Logout Person",
            "email": "logout@example.com",
            "password": "correcthorse123",
            "confirm_password": "correcthorse123",
        },
    )

    response = client.get("/auth/sign-out", follow_redirects=True)
    assert response.status_code == 200
    with client.session_transaction() as session:
        assert "_user_id" not in session


def test_authenticated_user_can_reach_gated_routes(client):
    client.post(
        "/auth/join",
        data={
            "display_name": "Gated Route Person",
            "email": "gated@example.com",
            "password": "correcthorse123",
            "confirm_password": "correcthorse123",
        },
    )

    response = client.get("/businesses/add")
    assert response.status_code == 200
