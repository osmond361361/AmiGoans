import re
from datetime import datetime, timezone

from app.extensions import db

STATUSES = ("pending", "approved", "rejected", "suspended")


class JobPost(db.Model):
    __tablename__ = "job_posts"

    id = db.Column(db.Integer, primary_key=True)
    posted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(170), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(150), nullable=False)
    job_url = db.Column(db.String(500), nullable=False)

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

    posted_by = db.relationship("User")

    def __repr__(self):
        return f"<JobPost {self.title} ({self.status})>"


def slugify(value):
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "job"


def unique_slug(title):
    base = slugify(title)
    slug = base
    suffix = 2
    while JobPost.query.filter_by(slug=slug).first() is not None:
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug
