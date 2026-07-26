from flask import render_template

from app.main import main_bp


@main_bp.route("/")
def home():
    # Stats panel removed until the community has 100+ registered members
    # (see main/home.html history). Re-add real DB-driven counts then.
    return render_template("main/home.html")


@main_bp.route("/about")
def about():
    return render_template("main/about.html")


@main_bp.route("/contact")
def contact():
    return render_template("main/contact.html")


@main_bp.route("/legal")
def legal():
    return render_template("main/legal.html")
