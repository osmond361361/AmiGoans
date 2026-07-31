from datetime import datetime, timezone

from app.extensions import db

CATEGORIES = ("church", "temple", "mosque", "school", "other")
STATUSES = ("pending", "approved", "rejected", "suspended")


class VillageLandmark(db.Model):
    __tablename__ = "village_landmarks"

    id = db.Column(db.Integer, primary_key=True)
    village_id = db.Column(db.Integer, db.ForeignKey("villages.id"), nullable=False, index=True)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    category = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(20), nullable=False, default="pending", index=True)

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    village = db.relationship("Village", backref=db.backref("landmarks", lazy="dynamic"))
    submitted_by = db.relationship("User")

    def __repr__(self):
        return f"<VillageLandmark {self.name} ({self.status})>"
