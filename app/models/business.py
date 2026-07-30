import re
from datetime import datetime, timezone

from app.extensions import db

CATEGORIES = ("Restaurants", "Travel", "Shopping", "Services", "Events", "Real Estate", "Other")
STATUSES = ("pending", "approved", "rejected", "suspended")


class Business(db.Model):
    __tablename__ = "businesses"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(170), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)

    telephone = db.Column(db.String(30), nullable=True)
    whatsapp = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    facebook_url = db.Column(db.String(255), nullable=True)

    town = db.Column(db.String(100), nullable=False)
    county = db.Column(db.String(100), nullable=True)
    nation = db.Column(db.String(30), nullable=False)
    postcode_district = db.Column(db.String(10), nullable=True)

    logo = db.Column(db.String(255), nullable=True)
    cover_image = db.Column(db.String(255), nullable=True)

    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    featured = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner = db.relationship("User")

    def __repr__(self):
        return f"<Business {self.name} ({self.status})>"


def slugify(value):
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "business"


def unique_slug(name):
    base = slugify(name)
    slug = base
    suffix = 2
    while Business.query.filter_by(slug=slug).first() is not None:
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug
