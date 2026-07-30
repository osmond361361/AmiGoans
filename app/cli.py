from datetime import datetime, timedelta, timezone

import click

from app.extensions import db
from app.models import SiteVisit, User


def register_cli_commands(app):
    @app.cli.command("create-admin")
    @click.argument("email")
    def create_admin(email):
        """Grant admin access to an existing user account, by email."""
        user = User.query.filter_by(email=email.lower().strip()).first()
        if user is None:
            click.echo(f"No account found for {email}. Ask them to join first, then rerun this.")
            return
        user.is_admin = True
        db.session.commit()
        click.echo(f"{user.email} is now an admin.")

    @app.cli.command("prune-old-visits")
    def prune_old_visits():
        """Delete site-visit records older than 12 months (Privacy Policy retention limit).

        Run this monthly, e.g. from cron.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=365)
        deleted = SiteVisit.query.filter(SiteVisit.visited_at < cutoff).delete()
        db.session.commit()
        click.echo(f"Deleted {deleted} site visit record(s) older than {cutoff.date()}.")
