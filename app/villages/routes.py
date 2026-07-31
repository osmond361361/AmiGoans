import os
import uuid

from flask import current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from PIL import Image

from app.extensions import db
from app.models.village import Village
from app.models.village_landmark import VillageLandmark
from app.models.village_photo import VillagePhoto
from app.villages import villages_bp
from app.villages.forms import VillageLandmarkForm, VillagePhotoForm

CATEGORY_LABELS = {
    "church": "Churches",
    "temple": "Temples",
    "mosque": "Mosques",
    "school": "Schools",
    "other": "Other Landmarks",
}


def _save_village_photo(file_storage):
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "village-photos")
    os.makedirs(upload_dir, exist_ok=True)

    max_dimension = 1600
    image = Image.open(file_storage.stream).convert("RGB")
    width, height = image.size
    if max(width, height) > max_dimension:
        scale = max_dimension / max(width, height)
        image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)

    filename = f"village-{uuid.uuid4().hex[:10]}.jpg"
    image.save(os.path.join(upload_dir, filename), "JPEG", quality=88)
    return filename


@villages_bp.route("/")
def index():
    villages = Village.query.order_by(Village.name).all()
    villages_json = [
        {"name": v.name, "slug": v.slug, "taluka": v.taluka, "district": v.district}
        for v in villages
    ]
    return render_template(
        "villages/index.html", villages_json=villages_json, village_count=len(villages)
    )


@villages_bp.route("/<slug>")
def detail(slug):
    village = Village.query.filter_by(slug=slug).first_or_404()
    landmarks = (
        VillageLandmark.query.filter_by(village_id=village.id, status="approved")
        .order_by(VillageLandmark.category, VillageLandmark.name)
        .all()
    )
    photos = (
        VillagePhoto.query.filter_by(village_id=village.id, status="approved")
        .order_by(VillagePhoto.created_at.desc())
        .all()
    )

    landmarks_by_category = {}
    for landmark in landmarks:
        landmarks_by_category.setdefault(landmark.category, []).append(landmark)

    return render_template(
        "villages/detail.html",
        village=village,
        landmarks_by_category=landmarks_by_category,
        category_labels=CATEGORY_LABELS,
        photos=photos,
    )


@villages_bp.route("/<slug>/landmarks/add", methods=["GET", "POST"])
@login_required
def add_landmark(slug):
    village = Village.query.filter_by(slug=slug).first_or_404()
    form = VillageLandmarkForm()

    if form.validate_on_submit():
        landmark = VillageLandmark(
            village_id=village.id,
            submitted_by_id=current_user.id,
            category=form.category.data,
            name=form.name.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            status="pending",
        )
        db.session.add(landmark)
        db.session.commit()
        flash(
            "Thanks! Your landmark has been submitted and is awaiting admin approval.",
            "success",
        )
        return redirect(url_for("villages.detail", slug=village.slug))

    return render_template("villages/landmark_add.html", form=form, village=village)


@villages_bp.route("/<slug>/photos/add", methods=["GET", "POST"])
@login_required
def add_photo(slug):
    village = Village.query.filter_by(slug=slug).first_or_404()
    form = VillagePhotoForm()

    if form.validate_on_submit():
        if not form.image.data:
            form.image.errors.append("Please choose a photo to upload.")
        else:
            photo = VillagePhoto(
                village_id=village.id,
                submitted_by_id=current_user.id,
                caption=form.caption.data.strip(),
                image=_save_village_photo(form.image.data),
                status="pending",
            )
            db.session.add(photo)
            db.session.commit()
            flash(
                "Thanks for sharing! Your photo has been submitted and is awaiting admin "
                "approval.",
                "success",
            )
            return redirect(url_for("villages.detail", slug=village.slug))

    return render_template("villages/photo_add.html", form=form, village=village)


@villages_bp.route("/mine")
@login_required
def my_submissions():
    landmarks = (
        VillageLandmark.query.filter_by(submitted_by_id=current_user.id)
        .order_by(VillageLandmark.created_at.desc())
        .all()
    )
    photos = (
        VillagePhoto.query.filter_by(submitted_by_id=current_user.id)
        .order_by(VillagePhoto.created_at.desc())
        .all()
    )
    return render_template("villages/my_submissions.html", landmarks=landmarks, photos=photos)
