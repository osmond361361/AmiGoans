"""Update Privacy Policy for IP geolocation in admin reports

Revision ID: 7a2c1e9d4f3b
Revises: 3f714742fc3e
Create Date: 2026-07-31 09:20:00.000000

"""
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7a2c1e9d4f3b"
down_revision = "3f714742fc3e"
branch_labels = None
depends_on = None


PAGES_TABLE = sa.table(
    "pages",
    sa.column("slug", sa.String),
    sa.column("content_html", sa.Text),
    sa.column("updated_at", sa.DateTime),
)

OLD_SERVER_LOGS_BULLET = (
    "<li><strong>Server access logs:</strong> every page request is logged with the visiting "
    "device's IP address, the page visited, the date/time, and browser information (user "
    "agent), for site security and operational purposes. If you're signed in when you visit, "
    "that visit is linked to your account.</li>"
)

NEW_SERVER_LOGS_BULLET = (
    OLD_SERVER_LOGS_BULLET
    + "\n  <li><strong>Approximate location from IP (admin reporting only):</strong> when "
    "generating internal traffic reports, an admin may resolve a visiting IP address to an "
    "approximate city and country using a third-party lookup service (ip-api.com). This is "
    "used only for operational reporting, is not linked to advertising, and is not shared "
    "with any other third party.</li>"
)


def upgrade():
    connection = op.get_bind()
    row = connection.execute(
        sa.select(PAGES_TABLE.c.content_html).where(PAGES_TABLE.c.slug == "privacy-policy")
    ).first()
    if row is None:
        return

    updated_content = row.content_html.replace(OLD_SERVER_LOGS_BULLET, NEW_SERVER_LOGS_BULLET)
    op.execute(
        PAGES_TABLE.update()
        .where(PAGES_TABLE.c.slug == "privacy-policy")
        .values(content_html=updated_content, updated_at=datetime.now(timezone.utc))
    )


def downgrade():
    connection = op.get_bind()
    row = connection.execute(
        sa.select(PAGES_TABLE.c.content_html).where(PAGES_TABLE.c.slug == "privacy-policy")
    ).first()
    if row is None:
        return

    reverted_content = row.content_html.replace(NEW_SERVER_LOGS_BULLET, OLD_SERVER_LOGS_BULLET)
    op.execute(
        PAGES_TABLE.update()
        .where(PAGES_TABLE.c.slug == "privacy-policy")
        .values(content_html=reverted_content, updated_at=datetime.now(timezone.utc))
    )
