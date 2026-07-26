from flask import Blueprint

members_bp = Blueprint("members", __name__, template_folder="../templates/members")

from app.members import routes  # noqa: E402,F401
