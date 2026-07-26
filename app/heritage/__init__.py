from flask import Blueprint

heritage_bp = Blueprint("heritage", __name__, template_folder="../templates/heritage")

from app.heritage import routes  # noqa: E402,F401
