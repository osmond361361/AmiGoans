from datetime import datetime, timezone

from app.extensions import db

STATUSES = ("pending", "approved", "rejected", "suspended")


class VillagePhoto(db.Model):
    __tablename__ = "village_photos"

    id = db.Column(db.Integer, primary_key=True)
    village_id = db.Column(db.Integer, db.ForeignKey("villages.id"), nullable=False, index=True)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    caption = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=False)

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

    village = db.relationship("Village", backref=db.backref("photos", lazy="dynamic"))
    submitted_by = db.relationship("User")

    def __repr__(self):
        return f"<VillagePhoto {self.id} ({self.status})>"
