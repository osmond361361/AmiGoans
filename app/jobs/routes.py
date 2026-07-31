from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.jobs import jobs_bp
from app.jobs.forms import JobForm
from app.models.job import JobPost, unique_slug


def _apply_form_to_job(form, job):
    job.title = form.title.data.strip()
    job.location = form.location.data.strip()
    job.job_url = form.job_url.data.strip()
    job.description = form.description.data.strip() if form.description.data else None


@jobs_bp.route("/")
def index():
    query = JobPost.query.filter_by(status="approved")

    search_term = request.args.get("q", "").strip()
    if search_term:
        like = f"%{search_term}%"
        query = query.filter(db.or_(JobPost.title.ilike(like), JobPost.location.ilike(like)))

    page = request.args.get("page", 1, type=int)
    listings = query.order_by(JobPost.created_at.desc()).paginate(page=page, per_page=12)

    return render_template("jobs/index.html", listings=listings)


@jobs_bp.route("/mine")
@login_required
def my_jobs():
    listings = (
        JobPost.query.filter_by(posted_by_id=current_user.id)
        .order_by(JobPost.created_at.desc())
        .all()
    )
    return render_template("jobs/my_jobs.html", listings=listings)


@jobs_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    form = JobForm()

    if form.validate_on_submit():
        job = JobPost(
            posted_by_id=current_user.id,
            slug=unique_slug(form.title.data.strip()),
            status="pending",
        )
        _apply_form_to_job(form, job)
        db.session.add(job)
        db.session.commit()
        flash(
            "Thanks! Your job link has been submitted and is awaiting admin approval.",
            "success",
        )
        return redirect(url_for("jobs.my_jobs"))

    return render_template("jobs/add.html", form=form)


@jobs_bp.route("/<slug>/edit", methods=["GET", "POST"])
@login_required
def edit(slug):
    job = JobPost.query.filter_by(slug=slug).first_or_404()
    if job.posted_by_id != current_user.id and not current_user.is_admin:
        abort(403)

    form = JobForm(obj=job)
    if form.validate_on_submit():
        _apply_form_to_job(form, job)
        db.session.commit()
        flash("Your job listing has been updated.", "success")
        return redirect(url_for("jobs.my_jobs"))

    return render_template("jobs/edit.html", form=form, job=job)


@jobs_bp.route("/<slug>")
def detail(slug):
    job = JobPost.query.filter_by(slug=slug).first_or_404()

    is_owner = current_user.is_authenticated and job.posted_by_id == current_user.id
    is_admin = current_user.is_authenticated and current_user.is_admin
    if job.status != "approved" and not (is_owner or is_admin):
        abort(404)

    return render_template("jobs/detail.html", job=job)
