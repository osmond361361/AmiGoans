from datetime import datetime, timezone

from app.extensions import db


class NewsletterSubscriber(db.Model):
    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    subscribed_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<NewsletterSubscriber {self.email}>"
