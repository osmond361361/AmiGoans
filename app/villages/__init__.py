from flask import Blueprint

villages_bp = Blueprint("villages", __name__, template_folder="../templates/villages")

from app.villages import routes  # noqa: E402,F401
