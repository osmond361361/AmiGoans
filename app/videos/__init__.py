from flask import Blueprint

videos_bp = Blueprint("videos", __name__, template_folder="../templates/videos")

from app.videos import routes  # noqa: E402,F401
