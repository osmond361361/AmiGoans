from datetime import datetime, timezone

from app.extensions import db


class Village(db.Model):
    __tablename__ = "villages"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False, index=True)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    taluka = db.Column(db.String(60), nullable=False, index=True)
    district = db.Column(db.String(60), nullable=False, index=True)
    gram_panchayat = db.Column(db.String(150), nullable=True)
    category = db.Column(db.String(20), nullable=True)

    population = db.Column(db.Integer, nullable=True)
    population_source = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<Village {self.name} ({self.taluka})>"
