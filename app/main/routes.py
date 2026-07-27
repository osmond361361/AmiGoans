from flask import flash, redirect, render_template, request, url_for

from app.extensions import db
from app.main import main_bp
from app.main.forms import NewsletterForm
from app.models import NewsletterSubscriber


@main_bp.route("/")
def home():
    return render_template("main/home.html")


@main_bp.route("/about")
def about():
    return render_template("main/about.html")


@main_bp.route("/motto")
def motto():
    return render_template("main/motto.html")


@main_bp.route("/contact")
def contact():
    return render_template("main/contact.html")


@main_bp.route("/legal")
def legal():
    return render_template("main/legal.html")


@main_bp.route("/subscribe", methods=["POST"])
def subscribe():
    form = NewsletterForm()
    next_url = request.referrer if request.referrer else url_for("main.home")

    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if not NewsletterSubscriber.query.filter_by(email=email).first():
            db.session.add(NewsletterSubscriber(email=email))
            db.session.commit()
        flash("Thanks for subscribing! We'll keep you posted.", "success")
    else:
        flash("Please enter a valid email address.", "danger")

    return redirect(next_url)
