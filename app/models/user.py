from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)

    oauth_provider = db.Column(db.String(20), nullable=True)
    oauth_id = db.Column(db.String(255), nullable=True)
    oauth_picture_url = db.Column(db.String(500), nullable=True)

    profile_photo = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(30), nullable=True)
    sms_marketing_consent = db.Column(db.Boolean, nullable=False, default=False)
    sms_consent_at = db.Column(db.DateTime(timezone=True), nullable=True)

    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def avatar_url(self):
        if self.profile_photo:
            from flask import url_for

            return url_for("static", filename=f"uploads/profiles/{self.profile_photo}")
        return self.oauth_picture_url

    __table_args__ = (
        db.UniqueConstraint("oauth_provider", "oauth_id", name="uq_user_oauth_identity"),
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.email}>"
