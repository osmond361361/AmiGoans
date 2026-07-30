from datetime import datetime, timezone

from app.extensions import db


class SiteVisit(db.Model):
    __tablename__ = "site_visits"

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(500), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    user_agent = db.Column(db.String(500), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    visited_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    user = db.relationship("User")

    def __repr__(self):
        return f"<SiteVisit {self.ip_address} {self.path}>"
