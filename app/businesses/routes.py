import os
import uuid

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from PIL import Image

from app.businesses import businesses_bp
from app.businesses.forms import BusinessForm
from app.extensions import db
from app.models.business import Business, unique_slug


def _save_business_image(file_storage, subfolder, size):
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(upload_dir, exist_ok=True)

    image = Image.open(file_storage.stream).convert("RGB")
    width, height = image.size
    target_ratio = size[0] / size[1]
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        image = image.crop((left, 0, left + new_width, height))
    else:
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        image = image.crop((0, top, width, top + new_height))

    image = image.resize(size, Image.LANCZOS)
    filename = f"business-{subfolder}-{uuid.uuid4().hex[:10]}.jpg"
    image.save(os.path.join(upload_dir, filename), "JPEG", quality=85)
    return filename


def _delete_business_image(filename, subfolder):
    if not filename:
        return
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder, filename)
    if os.path.exists(path):
        os.remove(path)


def _apply_form_to_business(form, business):
    business.name = form.name.data.strip()
    business.description = form.description.data.strip()
    business.category = form.category.data
    business.telephone = form.telephone.data.strip() if form.telephone.data else None
    business.whatsapp = form.whatsapp.data.strip() if form.whatsapp.data else None
    business.email = form.email.data.strip() if form.email.data else None
    business.website = form.website.data.strip() if form.website.data else None
    business.facebook_url = form.facebook_url.data.strip() if form.facebook_url.data else None
    business.town = form.town.data.strip()
    business.county = form.county.data.strip() if form.county.data else None
    business.nation = form.nation.data
    business.postcode_district = (
        form.postcode_district.data.strip().upper() if form.postcode_district.data else None
    )

    if form.logo.data:
        old_logo = business.logo
        business.logo = _save_business_image(form.logo.data, "business-logos", (300, 300))
        _delete_business_image(old_logo, "business-logos")

    if form.cover_image.data:
        old_cover = business.cover_image
        business.cover_image = _save_business_image(
            form.cover_image.data, "business-covers", (800, 450)
        )
        _delete_business_image(old_cover, "business-covers")


@businesses_bp.route("/")
def directory():
    query = Business.query.filter_by(status="approved")

    search_term = request.args.get("q", "").strip()
    if search_term:
        like = f"%{search_term}%"
        query = query.filter(db.or_(Business.name.ilike(like), Business.description.ilike(like)))

    for field in ("nation", "county", "town", "category"):
        value = request.args.get(field, "").strip()
        if value:
            query = query.filter(getattr(Business, field) == value)

    page = request.args.get("page", 1, type=int)
    listings = query.order_by(Business.created_at.desc()).paginate(page=page, per_page=12)

    featured = (
        Business.query.filter_by(status="approved", featured=True)
        .order_by(Business.created_at.desc())
        .limit(3)
        .all()
    )

    return render_template("businesses/directory.html", listings=listings, featured=featured)


@businesses_bp.route("/mine")
@login_required
def my_businesses():
    listings = (
        Business.query.filter_by(owner_id=current_user.id)
        .order_by(Business.created_at.desc())
        .all()
    )
    return render_template("businesses/my_businesses.html", listings=listings)


@businesses_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    form = BusinessForm()

    if form.validate_on_submit():
        business = Business(
            owner_id=current_user.id,
            slug=unique_slug(form.name.data.strip()),
            nation=form.nation.data,
            town=form.town.data.strip(),
            category=form.category.data,
            name=form.name.data.strip(),
            description=form.description.data.strip(),
            status="pending",
        )
        _apply_form_to_business(form, business)
        db.session.add(business)
        db.session.commit()
        flash(
            "Thanks! Your business has been submitted and is awaiting admin approval.",
            "success",
        )
        return redirect(url_for("businesses.my_businesses"))

    return render_template("businesses/add.html", form=form)


@businesses_bp.route("/<slug>/edit", methods=["GET", "POST"])
@login_required
def edit(slug):
    business = Business.query.filter_by(slug=slug).first_or_404()
    if business.owner_id != current_user.id and not current_user.is_admin:
        abort(403)

    form = BusinessForm(obj=business)
    if form.validate_on_submit():
        _apply_form_to_business(form, business)
        db.session.commit()
        flash("Your business listing has been updated.", "success")
        return redirect(url_for("businesses.my_businesses"))

    return render_template("businesses/edit.html", form=form, business=business)


@businesses_bp.route("/<slug>")
def detail(slug):
    business = Business.query.filter_by(slug=slug).first_or_404()

    is_owner = current_user.is_authenticated and business.owner_id == current_user.id
    is_admin = current_user.is_authenticated and current_user.is_admin
    if business.status != "approved" and not (is_owner or is_admin):
        abort(404)

    return render_template("businesses/detail.html", business=business)
