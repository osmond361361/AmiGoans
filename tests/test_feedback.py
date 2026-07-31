from unittest.mock import patch

from app.extensions import db
from app.models import Feedback, User


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


def test_submitting_an_idea_creates_a_feedback_entry(client, app):
    _make_user(app, "member@example.com")
    _sign_in(client, "member@example.com")

    response = client.post(
        "/contribute/idea",
        data={
            "title": "Dark mode please",
            "description": "It would be great to have a dark mode option.",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        idea = Feedback.query.filter_by(kind="idea").first()
        assert idea is not None
        assert idea.title == "Dark mode please"
        assert idea.status == "new"


def test_submitting_an_issue_creates_a_feedback_entry_with_page_url(client, app):
    _make_user(app, "member2@example.com")
    _sign_in(client, "member2@example.com")

    response = client.post(
        "/contribute/issue",
        data={
            "description": "The submit button doesn't work on mobile.",
            "page_url": "https://amigoans.co.uk/businesses/",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        issue = Feedback.query.filter_by(kind="issue").first()
        assert issue is not None
        assert issue.page_url == "https://amigoans.co.uk/businesses/"
        assert issue.status == "new"


def test_feedback_list_requires_admin(client, app):
    _make_user(app, "member3@example.com", is_admin=False)
    _sign_in(client, "member3@example.com")

    response = client.get("/admin/feedback/idea")
    assert response.status_code == 403


def test_feedback_list_rejects_unknown_kind(client, app):
    _make_user(app, "admin@example.com", is_admin=True)
    _sign_in(client, "admin@example.com")

    response = client.get("/admin/feedback/nonsense")
    assert response.status_code == 404


@patch("app.admin.routes.send_feedback_response_email")
def test_admin_can_respond_to_an_idea_and_it_emails_the_submitter(mock_send, client, app):
    submitter_id = _make_user(app, "member4@example.com")
    _make_user(app, "admin2@example.com", is_admin=True)

    with app.app_context():
        feedback = Feedback(
            submitted_by_id=submitter_id,
            kind="idea",
            title="Dark mode please",
            description="It would be great to have a dark mode option.",
            status="new",
        )
        db.session.add(feedback)
        db.session.commit()
        feedback_id = feedback.id

    _sign_in(client, "admin2@example.com")
    response = client.post(
        f"/admin/feedback/item/{feedback_id}",
        data={
            "status": "resolved",
            "admin_response": "Great idea, we've added it to the roadmap!",
            "send_response": "1",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    mock_send.assert_called_once()

    with app.app_context():
        updated = db.session.get(Feedback, feedback_id)
        assert updated.status == "resolved"
        assert updated.admin_response == "Great idea, we've added it to the roadmap!"
        assert updated.responded_at is not None


@patch("app.admin.routes.send_feedback_response_email")
def test_admin_save_only_does_not_send_email(mock_send, client, app):
    submitter_id = _make_user(app, "member5@example.com")
    _make_user(app, "admin3@example.com", is_admin=True)

    with app.app_context():
        feedback = Feedback(
            submitted_by_id=submitter_id,
            kind="issue",
            description="Something is broken.",
            status="new",
        )
        db.session.add(feedback)
        db.session.commit()
        feedback_id = feedback.id

    _sign_in(client, "admin3@example.com")
    response = client.post(
        f"/admin/feedback/item/{feedback_id}",
        data={"status": "in_progress", "admin_response": "", "save_only": "1"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    mock_send.assert_not_called()

    with app.app_context():
        updated = db.session.get(Feedback, feedback_id)
        assert updated.status == "in_progress"
        assert updated.responded_at is None
