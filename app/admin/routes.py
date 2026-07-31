import csv
import io
from datetime import datetime, timedelta, timezone

from flask import Response, abort, flash, redirect, render_template, request, url_for

from app.admin import admin_bp
from app.admin.decorators import admin_required
from app.admin.forms import PageForm
from app.admin.geolocation import resolve_ip_location
from app.extensions import db
from app.models import Page, SiteVisit, User
from app.models.business import STATUSES, Business
from app.models.job import STATUSES as JOB_STATUSES
from app.models.job import JobPost


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

    return render_template(
        "admin/index.html",
        total_hits=total_hits,
        unique_ips=unique_ips,
        hits_today=hits_today,
        hits_this_week=hits_this_week,
        recent_visits=recent_visits,
        pending_businesses=pending_businesses,
        pending_jobs=pending_jobs,
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

    return render_template(
        "admin/reports.html",
        total_users=total_users,
        new_users_week=new_users_week,
        new_users_month=new_users_month,
        total_hits=total_hits,
        unique_ips=unique_ips,
        hits_today=hits_today,
        hits_this_week=hits_this_week,
        start=request.args.get("start", ""),
        end=request.args.get("end", ""),
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
