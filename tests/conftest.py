import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app(tmp_path):
    app = create_app("testing")
    app.config["UPLOAD_FOLDER"] = str(tmp_path / "uploads")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def no_real_wikipedia_calls(monkeypatch):
    """Tests must never hit the real Wikipedia API -- default to 'no match'.

    Individual tests can still override this via `monkeypatch.setattr(...)`
    with a fake return value to exercise the caching/rendering behaviour.
    """
    monkeypatch.setattr("app.villages.routes.fetch_village_wikipedia", lambda *a, **k: None)
