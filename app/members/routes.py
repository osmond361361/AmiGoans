from flask import render_template

from app.members import members_bp


@members_bp.route("/")
def index():
    # Stage 3 adds the real member directory. This is the visual shell only.
    return render_template("members/index.html")
