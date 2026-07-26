from flask import render_template
from flask_login import login_required

from app.businesses import businesses_bp


@businesses_bp.route("/")
def directory():
    # Stage 4 adds the real business directory, search and filters.
    return render_template("businesses/directory.html")


@businesses_bp.route("/add")
@login_required
def add():
    # Adding a business requires a registered account. No one can be
    # authenticated yet (Stage 3 adds real accounts), so this always
    # redirects to sign-in for now -- that's correct, not a bug.
    return render_template("businesses/add.html")
