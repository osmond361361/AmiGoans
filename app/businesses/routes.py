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
    return render_template("businesses/add.html")
