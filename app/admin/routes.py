from datetime import datetime, timedelta, timezone

from flask import abort, flash, redirect, render_template, request, url_for

from app.admin import admin_bp
from app.admin.decorators import admin_required
from app.admin.forms import PageForm
from app.extensions import db
from app.models import Page, SiteVisit
from app.models.business import STATUSES, Business


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

    return render_template(
        "admin/index.html",
        total_hits=total_hits,
        unique_ips=unique_ips,
        hits_today=hits_today,
        hits_this_week=hits_this_week,
        recent_visits=recent_visits,
        pending_businesses=pending_businesses,
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
