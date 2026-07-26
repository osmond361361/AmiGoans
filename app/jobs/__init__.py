from flask import Blueprint

jobs_bp = Blueprint("jobs", __name__, template_folder="../templates/jobs")

from app.jobs import routes  # noqa: E402,F401
