from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.main import main_bp
from app.main.forms import IdeaForm, IssueForm, NewsletterForm
from app.models import Feedback, NewsletterSubscriber, Page


@main_bp.route("/")
def home():
    return render_template("main/home.html")


@main_bp.route("/about")
def about():
    return render_template("main/about.html", page=Page.query.filter_by(slug="about").first())


@main_bp.route("/contribute")
@login_required
def contribute():
    return render_template("main/contribute.html")


@main_bp.route("/contribute/idea", methods=["GET", "POST"])
@login_required
def share_idea():
    form = IdeaForm()

    if form.validate_on_submit():
        db.session.add(
            Feedback(
                submitted_by_id=current_user.id,
                kind="idea",
                title=form.title.data.strip(),
                description=form.description.data.strip(),
                status="new",
            )
        )
        db.session.commit()
        flash("Thanks for the idea! Our admins will take a look.", "success")
        return redirect(url_for("main.contribute"))

    return render_template("main/share_idea.html", form=form)


@main_bp.route("/contribute/issue", methods=["GET", "POST"])
@login_required
def report_issue():
    form = IssueForm()
    if request.method == "GET" and not form.page_url.data:
        form.page_url.data = request.referrer or ""

    if form.validate_on_submit():
        db.session.add(
            Feedback(
                submitted_by_id=current_user.id,
                kind="issue",
                description=form.description.data.strip(),
                page_url=form.page_url.data.strip() if form.page_url.data else None,
                status="new",
            )
        )
        db.session.commit()
        flash("Thanks for letting us know! Our admins will look into it.", "success")
        return redirect(url_for("main.contribute"))

    return render_template("main/report_issue.html", form=form)


@main_bp.route("/motto")
def motto():
    return render_template("main/motto.html", page=Page.query.filter_by(slug="motto").first())


@main_bp.route("/contact")
def contact():
    return render_template("main/contact.html", page=Page.query.filter_by(slug="contact").first())


@main_bp.route("/legal")
def legal():
    pages = {
        page.slug: page
        for page in Page.query.filter(
            Page.slug.in_(["privacy-policy", "terms-conditions", "community-guidelines"])
        ).all()
    }
    return render_template(
        "main/legal.html",
        privacy_page=pages.get("privacy-policy"),
        terms_page=pages.get("terms-conditions"),
        guidelines_page=pages.get("community-guidelines"),
    )


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
