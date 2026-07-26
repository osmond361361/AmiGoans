from flask import render_template

from app.admin import admin_bp


@admin_bp.route("/")
def index():
    # Stage 3+ adds real role-based access control and admin actions.
    # This route is unprotected in Stage 1 because there is no auth yet.
    return render_template("admin/index.html")
