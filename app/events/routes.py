from flask import render_template

from app.events import events_bp


@events_bp.route("/")
def index():
    # Stage 5 adds real UK Goan events.
    return render_template("events/index.html")
