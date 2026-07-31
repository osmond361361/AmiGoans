from datetime import datetime, timezone

from app.extensions import db


class IpLocation(db.Model):
    __tablename__ = "ip_locations"

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), unique=True, nullable=False, index=True)
    city = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    is_private = db.Column(db.Boolean, nullable=False, default=False)
    looked_up_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<IpLocation {self.ip_address}>"
