import csv
import io
from datetime import datetime, timedelta, timezone

from flask import Response, abort, flash, redirect, render_template, request, url_for

from app.admin import admin_bp
from app.admin.decorators import admin_required
from app.admin.feedback_email import send_feedback_response_email
from app.admin.forms import FeedbackResponseForm, PageForm
from app.admin.geolocation import resolve_ip_location
from app.extensions import db
from app.models import Page, SiteVisit, User
from app.models.business import STATUSES, Business
from app.models.feedback import STATUSES as FEEDBACK_STATUSES
from app.models.feedback import Feedback
from app.models.job import STATUSES as JOB_STATUSES
from app.models.job import JobPost
from app.models.photo import STATUSES as PHOTO_STATUSES
from app.models.photo import Photo
from app.models.recipe import STATUSES as RECIPE_STATUSES
from app.models.recipe import Recipe
from app.models.story import STATUSES as STORY_STATUSES
from app.models.story import Story


def _parse_date_range():
    """Read ?start=YYYY-MM-DD&end=YYYY-MM-DD, ignoring anything unparsable."""
    start_dt = None
    end_dt = None
    start_str = request.args.get("start", "").strip()
    end_str = request.args.get("end", "").strip()

    try:
        if start_str:
            start_dt = datetime.strptime(start_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if end_str:
            end_dt = datetime.strptime(end_str, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            ) + timedelta(days=1)
    except ValueError:
        return None, None

    return start_dt, end_dt


def _status_filter():
    """Read ?status=pending/approved/rejected/suspended; anything else means no filter."""
    status = request.args.get("status", "")
    return status if status in STATUSES else None


@admin_bp.route("/")
@admin_required
def index():
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    total_hits = db.session.query(SiteVisit).count()
    unique_ips = db.session.query(SiteVisit.ip_address).distinct().count()
    hits_today = db.session.query(SiteVisit).filter(SiteVisit.visited_at >= today_start).count()
    hits_this_week = db.session.query(SiteVisit).filter(SiteVisit.visited_at >= week_start).count()

    page = request.args.get("page", 1, type=int)
    recent_visits = SiteVisit.query.order_by(SiteVisit.visited_at.desc()).paginate(
        page=page, per_page=50
    )

    pending_businesses = Business.query.filter_by(status="pending").count()
    pending_jobs = JobPost.query.filter_by(status="pending").count()
    pending_stories = Story.query.filter_by(status="pending").count()
    pending_recipes = Recipe.query.filter_by(status="pending").count()
    pending_photos = Photo.query.filter_by(status="pending").count()
    pending_ideas = Feedback.query.filter_by(kind="idea", status="new").count()
    pending_issues = Feedback.query.filter_by(kind="issue", status="new").count()

    return render_template(
        "admin/index.html",
        total_hits=total_hits,
        unique_ips=unique_ips,
        hits_today=hits_today,
        hits_this_week=hits_this_week,
        recent_visits=recent_visits,
        pending_businesses=pending_businesses,
        pending_jobs=pending_jobs,
        pending_stories=pending_stories,
        pending_recipes=pending_recipes,
        pending_photos=pending_photos,
        pending_ideas=pending_ideas,
        pending_issues=pending_issues,
    )


@admin_bp.route("/businesses")
@admin_required
def businesses():
    status_filter = request.args.get("status", "pending")
    query = Business.query
    if status_filter in STATUSES:
        query = query.filter_by(status=status_filter)

    page = request.args.get("page", 1, type=int)
    listings = query.order_by(Business.created_at.desc()).paginate(page=page, per_page=25)

    return render_template(
        "admin/businesses.html",
        listings=listings,
        status_filter=status_filter,
        statuses=STATUSES,
    )


@admin_bp.route("/businesses/<int:business_id>/status", methods=["POST"])
@admin_required
def update_business_status(business_id):
    business = Business.query.get_or_404(business_id)
    new_status = request.form.get("status")
    if new_status not in STATUSES:
        abort(400)

    business.status = new_status
    db.session.commit()
    flash(f'"{business.name}" is now {new_status}.', "success")
    return redirect(
        url_for("admin.businesses", status=request.form.get("return_status", "pending"))
    )


@admin_bp.route("/jobs")
@admin_required
def jobs():
    status_filter = request.args.get("status", "pending")
    query = JobPost.query
    if status_filter in JOB_STATUSES:
        query = query.filter_by(status=status_filter)

    page = request.args.get("page", 1, type=int)
    listings = query.order_by(JobPost.created_at.desc()).paginate(page=page, per_page=25)

    return render_template(
        "admin/jobs.html",
        listings=listings,
        status_filter=status_filter,
        statuses=JOB_STATUSES,
    )


@admin_bp.route("/jobs/<int:job_id>/status", methods=["POST"])
@admin_required
def update_job_status(job_id):
    job = JobPost.query.get_or_404(job_id)
    new_status = request.form.get("status")
    if new_status not in JOB_STATUSES:
        abort(400)

    job.status = new_status
    db.session.commit()
    flash(f'"{job.title}" is now {new_status}.', "success")
    return redirect(url_for("admin.jobs", status=request.form.get("return_status", "pending")))


@admin_bp.route("/stories")
@admin_required
def stories():
    status_filter = request.args.get("status", "pending")
    query = Story.query
    if status_filter in STORY_STATUSES:
        query = query.filter_by(status=status_filter)

    page = request.args.get("page", 1, type=int)
    listings = query.order_by(Story.created_at.desc()).paginate(page=page, per_page=25)

    return render_template(
        "admin/stories.html",
        listings=listings,
        status_filter=status_filter,
        statuses=STORY_STATUSES,
    )


@admin_bp.route("/stories/<int:story_id>/status", methods=["POST"])
@admin_required
def update_story_status(story_id):
    story = Story.query.get_or_404(story_id)
    new_status = request.form.get("status")
    if new_status not in STORY_STATUSES:
        abort(400)

    story.status = new_status
    db.session.commit()
    flash(f'"{story.title}" is now {new_status}.', "success")
    return redirect(url_for("admin.stories", status=request.form.get("return_status", "pending")))


@admin_bp.route("/recipes")
@admin_required
def recipes():
    status_filter = request.args.get("status", "pending")
    query = Recipe.query
    if status_filter in RECIPE_STATUSES:
        query = query.filter_by(status=status_filter)

    page = request.args.get("page", 1, type=int)
    listings = query.order_by(Recipe.created_at.desc()).paginate(page=page, per_page=25)

    return render_template(
        "admin/recipes.html",
        listings=listings,
        status_filter=status_filter,
        statuses=RECIPE_STATUSES,
    )


@admin_bp.route("/recipes/<int:recipe_id>/status", methods=["POST"])
@admin_required
def update_recipe_status(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    new_status = request.form.get("status")
    if new_status not in RECIPE_STATUSES:
        abort(400)

    recipe.status = new_status
    db.session.commit()
    flash(f'"{recipe.title}" is now {new_status}.', "success")
    return redirect(url_for("admin.recipes", status=request.form.get("return_status", "pending")))


@admin_bp.route("/photos")
@admin_required
def photos():
    status_filter = request.args.get("status", "pending")
    query = Photo.query
    if status_filter in PHOTO_STATUSES:
        query = query.filter_by(status=status_filter)

    page = request.args.get("page", 1, type=int)
    listings = query.order_by(Photo.created_at.desc()).paginate(page=page, per_page=25)

    return render_template(
        "admin/photos.html",
        listings=listings,
        status_filter=status_filter,
        statuses=PHOTO_STATUSES,
    )


@admin_bp.route("/photos/<int:photo_id>/status", methods=["POST"])
@admin_required
def update_photo_status(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    new_status = request.form.get("status")
    if new_status not in PHOTO_STATUSES:
        abort(400)

    photo.status = new_status
    db.session.commit()
    flash(f"Photo is now {new_status}.", "success")
    return redirect(url_for("admin.photos", status=request.form.get("return_status", "pending")))


@admin_bp.route("/feedback/<kind>")
@admin_required
def feedback_list(kind):
    if kind not in ("idea", "issue"):
        abort(404)

    status_filter = request.args.get("status", "new")
    query = Feedback.query.filter_by(kind=kind)
    if status_filter in FEEDBACK_STATUSES:
        query = query.filter_by(status=status_filter)

    page = request.args.get("page", 1, type=int)
    listings = query.order_by(Feedback.created_at.desc()).paginate(page=page, per_page=25)

    return render_template(
        "admin/feedback_list.html",
        listings=listings,
        status_filter=status_filter,
        statuses=FEEDBACK_STATUSES,
        kind=kind,
    )


@admin_bp.route("/feedback/item/<int:feedback_id>", methods=["GET", "POST"])
@admin_required
def feedback_detail(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    form = FeedbackResponseForm(obj=feedback)

    if form.validate_on_submit():
        feedback.status = form.status.data
        feedback.admin_response = (
            form.admin_response.data.strip() if form.admin_response.data else None
        )
        should_send = "send_response" in request.form and feedback.admin_response
        db.session.commit()

        if should_send:
            feedback.responded_at = datetime.now(timezone.utc)
            db.session.commit()
            try:
                send_feedback_response_email(feedback)
                flash("Response saved and emailed to the submitter.", "success")
            except Exception:
                flash("Response saved, but the email failed to send.", "danger")
        else:
            flash("Saved.", "success")

        return redirect(url_for("admin.feedback_list", kind=feedback.kind))

    return render_template("admin/feedback_detail.html", feedback=feedback, form=form)


@admin_bp.route("/pages")
@admin_required
def pages():
    listings = Page.query.order_by(Page.title).all()
    return render_template("admin/pages.html", listings=listings)


PAGE_VIEW_URLS = {
    "motto": "main.motto",
    "about": "main.about",
    "contact": "main.contact",
    "privacy-policy": "main.legal",
    "terms-conditions": "main.legal",
    "community-guidelines": "main.legal",
}
PAGE_VIEW_ANCHORS = {
    "privacy-policy": "privacy",
    "terms-conditions": "terms",
    "community-guidelines": "guidelines",
}


@admin_bp.route("/pages/<slug>/edit", methods=["GET", "POST"])
@admin_required
def edit_page(slug):
    page = Page.query.filter_by(slug=slug).first_or_404()
    form = PageForm(obj=page)

    if form.validate_on_submit():
        page.title = form.title.data.strip()
        page.content_html = form.content_html.data
        db.session.commit()
        flash(f'"{page.title}" has been updated.', "success")
        return redirect(url_for("admin.pages"))

    view_endpoint = PAGE_VIEW_URLS.get(slug)
    view_url = url_for(view_endpoint) if view_endpoint else None
    if view_url and slug in PAGE_VIEW_ANCHORS:
        view_url += f"#{PAGE_VIEW_ANCHORS[slug]}"

    return render_template("admin/edit_page.html", form=form, page=page, view_url=view_url)


@admin_bp.route("/reports")
@admin_required
def reports():
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    total_users = User.query.count()
    new_users_week = User.query.filter(User.created_at >= week_start).count()
    new_users_month = User.query.filter(User.created_at >= month_start).count()

    total_hits = db.session.query(SiteVisit).count()
    unique_ips = db.session.query(SiteVisit.ip_address).distinct().count()
    hits_today = db.session.query(SiteVisit).filter(SiteVisit.visited_at >= today_start).count()
    hits_this_week = db.session.query(SiteVisit).filter(SiteVisit.visited_at >= week_start).count()

    total_businesses = Business.query.count()
    total_jobs = JobPost.query.count()
    total_stories = Story.query.count()

    return render_template(
        "admin/reports.html",
        total_users=total_users,
        new_users_week=new_users_week,
        new_users_month=new_users_month,
        total_hits=total_hits,
        unique_ips=unique_ips,
        hits_today=hits_today,
        hits_this_week=hits_this_week,
        total_businesses=total_businesses,
        total_jobs=total_jobs,
        total_stories=total_stories,
        start=request.args.get("start", ""),
        end=request.args.get("end", ""),
        status=request.args.get("status", "all"),
        listing_statuses=STATUSES,
    )


@admin_bp.route("/reports/users.csv")
@admin_required
def users_csv():
    start_dt, end_dt = _parse_date_range()
    query = User.query
    if start_dt:
        query = query.filter(User.created_at >= start_dt)
    if end_dt:
        query = query.filter(User.created_at < end_dt)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["ID", "Email", "Display Name", "Admin", "Sign-in Method", "Registered At (UTC)"]
    )
    for user in query.order_by(User.created_at.asc()).all():
        sign_in_method = user.oauth_provider.capitalize() if user.oauth_provider else "Password"
        writer.writerow(
            [
                user.id,
                user.email,
                user.display_name,
                "Yes" if user.is_admin else "No",
                sign_in_method,
                user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=amigoans-users.csv"},
    )


@admin_bp.route("/reports/hits.csv")
@admin_required
def hits_csv():
    start_dt, end_dt = _parse_date_range()
    query = SiteVisit.query
    if start_dt:
        query = query.filter(SiteVisit.visited_at >= start_dt)
    if end_dt:
        query = query.filter(SiteVisit.visited_at < end_dt)

    location_cache = {}
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Time (UTC)",
            "IP Address",
            "City",
            "Region",
            "Country",
            "Path",
            "Signed-in As",
            "User Agent",
        ]
    )
    for visit in query.order_by(SiteVisit.visited_at.asc()).all():
        if visit.ip_address not in location_cache:
            location_cache[visit.ip_address] = resolve_ip_location(visit.ip_address)
        location = location_cache[visit.ip_address]
        writer.writerow(
            [
                visit.visited_at.strftime("%Y-%m-%d %H:%M:%S"),
                visit.ip_address,
                location["city"] or "",
                location["region"] or "",
                location["country"] or "",
                visit.path,
                visit.user.display_name if visit.user else "",
                visit.user_agent or "",
            ]
        )

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=amigoans-hits.csv"},
    )


@admin_bp.route("/reports/businesses.csv")
@admin_required
def businesses_csv():
    start_dt, end_dt = _parse_date_range()
    status = _status_filter()
    query = Business.query
    if start_dt:
        query = query.filter(Business.created_at >= start_dt)
    if end_dt:
        query = query.filter(Business.created_at < end_dt)
    if status:
        query = query.filter_by(status=status)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "ID",
            "Name",
            "Owner",
            "Owner Email",
            "Category",
            "Town",
            "County",
            "Nation",
            "Status",
            "Submitted At (UTC)",
        ]
    )
    for business in query.order_by(Business.created_at.asc()).all():
        writer.writerow(
            [
                business.id,
                business.name,
                business.owner.display_name,
                business.owner.email,
                business.category,
                business.town,
                business.county or "",
                business.nation,
                business.status,
                business.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=amigoans-businesses.csv"},
    )


@admin_bp.route("/reports/jobs.csv")
@admin_required
def jobs_csv():
    start_dt, end_dt = _parse_date_range()
    status = _status_filter()
    query = JobPost.query
    if start_dt:
        query = query.filter(JobPost.created_at >= start_dt)
    if end_dt:
        query = query.filter(JobPost.created_at < end_dt)
    if status:
        query = query.filter_by(status=status)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "ID",
            "Title",
            "Posted By",
            "Posted By Email",
            "Location",
            "Job Link",
            "Status",
            "Submitted At (UTC)",
        ]
    )
    for job in query.order_by(JobPost.created_at.asc()).all():
        writer.writerow(
            [
                job.id,
                job.title,
                job.posted_by.display_name,
                job.posted_by.email,
                job.location,
                job.job_url,
                job.status,
                job.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=amigoans-jobs.csv"},
    )


@admin_bp.route("/reports/stories.csv")
@admin_required
def stories_csv():
    start_dt, end_dt = _parse_date_range()
    status = _status_filter()
    query = Story.query
    if start_dt:
        query = query.filter(Story.created_at >= start_dt)
    if end_dt:
        query = query.filter(Story.created_at < end_dt)
    if status:
        query = query.filter_by(status=status)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["ID", "Title", "Author", "Author Email", "Status", "Submitted At (UTC)"])
    for story in query.order_by(Story.created_at.asc()).all():
        writer.writerow(
            [
                story.id,
                story.title,
                story.author.display_name,
                story.author.email,
                story.status,
                story.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=amigoans-stories.csv"},
    )
