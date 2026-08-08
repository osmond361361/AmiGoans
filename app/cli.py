import os
import time
from collections import Counter
from datetime import datetime, timedelta, timezone

import click

from app.extensions import db
from app.models import SiteVisit, User
from app.models.village import Village
from app.villages.wikipedia import clean_name, fetch_village_wikipedia


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

    @app.cli.command("fetch-village-wikipedia")
    @click.option("--refresh", is_flag=True, help="Re-fetch villages already checked before.")
    @click.option("--limit", type=int, default=None, help="Stop after this many villages.")
    def fetch_village_wikipedia_cmd(refresh, limit):
        """Backfill Village.wiki_* fields from Wikipedia for the whole directory.

        Safe to re-run: villages already checked are skipped unless --refresh
        is passed. Rate-limited to be polite to Wikipedia's API.
        """
        name_counts = Counter(clean_name(v.name).lower() for v in Village.query.all())

        query = Village.query.order_by(Village.name)
        if not refresh:
            query = query.filter(Village.wiki_checked_at.is_(None))
        villages = query.all() if limit is None else query.limit(limit).all()

        images_dir = os.path.join(app.static_folder, "images", "villages")
        matched = 0
        for i, village in enumerate(villages, start=1):
            has_conflict = name_counts[clean_name(village.name).lower()] > 1
            try:
                info = fetch_village_wikipedia(
                    village.name,
                    taluka=village.taluka,
                    require_taluka_match=has_conflict,
                    images_dir=images_dir,
                    slug=village.slug,
                )
            except Exception as exc:  # noqa: BLE001 - never let one bad lookup abort the run
                info = None
                click.echo(f"[{i}/{len(villages)}] {village.name}: error ({exc})")

            if info:
                for field, value in info.items():
                    setattr(village, field, value)
                matched += 1
                click.echo(f"[{i}/{len(villages)}] {village.name}: matched -> {info['wiki_url']}")
            else:
                click.echo(f"[{i}/{len(villages)}] {village.name}: no confident match")

            village.wiki_checked_at = datetime.now(timezone.utc)
            db.session.commit()
            time.sleep(0.3)

        click.echo(f"Done. {matched}/{len(villages)} villages matched to a Wikipedia article.")
