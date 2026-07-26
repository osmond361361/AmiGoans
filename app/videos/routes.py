from flask import render_template

from app.videos import videos_bp


@videos_bp.route("/")
def index():
    # Stage 5 adds real Ami Goans TV video/livestream embeds.
    return render_template("videos/index.html")
