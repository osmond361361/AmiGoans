from flask import Blueprint

businesses_bp = Blueprint("businesses", __name__, template_folder="../templates/businesses")

from app.businesses import routes  # noqa: E402,F401
