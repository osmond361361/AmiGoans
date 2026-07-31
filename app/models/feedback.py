from datetime import datetime, timezone

from app.extensions import db

KINDS = ("idea", "issue")
STATUSES = ("new", "in_progress", "resolved")


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    kind = db.Column(db.String(20), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=True)
    description = db.Column(db.Text, nullable=False)
    page_url = db.Column(db.String(500), nullable=True)

    status = db.Column(db.String(20), nullable=False, default="new", index=True)
    admin_response = db.Column(db.Text, nullable=True)
    responded_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    submitted_by = db.relationship("User")

    def __repr__(self):
        return f"<Feedback {self.kind} #{self.id} ({self.status})>"
