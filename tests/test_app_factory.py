def test_create_app_returns_app(app):
    assert app is not None
    assert app.config["TESTING"] is True


def test_blueprints_registered(app):
    expected = {
        "main",
        "auth",
        "members",
        "businesses",
        "events",
        "heritage",
        "videos",
        "jobs",
        "admin",
    }
    assert expected.issubset(set(app.blueprints.keys()))
