import os
import uuid
from datetime import datetime, timezone

from flask import current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from PIL import Image

from app.extensions import db
from app.members import members_bp
from app.members.forms import ProfileForm


@members_bp.route("/")
def index():
    # Stage 3 adds the real member directory. This is the visual shell only.
    return render_template("members/index.html")


def save_profile_photo(file_storage, user_id):
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "profiles")
    os.makedirs(upload_dir, exist_ok=True)

    image = Image.open(file_storage.stream).convert("RGB")

    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    image = image.resize((400, 400), Image.LANCZOS)

    filename = f"user-{user_id}-{uuid.uuid4().hex[:8]}.jpg"
    image.save(os.path.join(upload_dir, filename), "JPEG", quality=85)
    return filename


def delete_profile_photo(filename):
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], "profiles", filename)
    if os.path.exists(path):
        os.remove(path)


@members_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.display_name = form.display_name.data.strip()
        current_user.phone_number = (
            form.phone_number.data.strip() if form.phone_number.data else None
        )

        if form.sms_marketing_consent.data != current_user.sms_marketing_consent:
            current_user.sms_marketing_consent = form.sms_marketing_consent.data
            current_user.sms_consent_at = datetime.now(timezone.utc)

        photo_file = form.photo.data
        if photo_file:
            old_photo = current_user.profile_photo
            current_user.profile_photo = save_profile_photo(photo_file, current_user.id)
            if old_photo:
                delete_profile_photo(old_photo)

        db.session.commit()
        flash("Your profile has been updated.", "success")
        return redirect(url_for("members.profile"))

    return render_template("members/profile.html", form=form)
