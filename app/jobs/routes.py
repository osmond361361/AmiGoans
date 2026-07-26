from flask import render_template
from flask_login import login_required

from app.jobs import jobs_bp


@jobs_bp.route("/")
def index():
    # Community-posted job links. Real posting/moderation arrives in a
    # later stage; this is the visual shell only.
    return render_template("jobs/index.html")


@jobs_bp.route("/add")
@login_required
def add():
    # Recommending a job requires a registered account. No one can be
    # authenticated yet (Stage 3 adds real accounts), so this always
    # redirects to sign-in for now -- that's correct, not a bug.
    return render_template("jobs/add.html")
