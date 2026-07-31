import os
import uuid

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from PIL import Image

from app.extensions import db
from app.heritage import heritage_bp
from app.heritage.forms import StoryForm
from app.models.story import Story, unique_slug


def _save_story_image(file_storage):
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "story-covers")
    os.makedirs(upload_dir, exist_ok=True)

    size = (800, 450)
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
    filename = f"story-cover-{uuid.uuid4().hex[:10]}.jpg"
    image.save(os.path.join(upload_dir, filename), "JPEG", quality=85)
    return filename


def _delete_story_image(filename):
    if not filename:
        return
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], "story-covers", filename)
    if os.path.exists(path):
        os.remove(path)


def _apply_form_to_story(form, story):
    story.title = form.title.data.strip()
    story.body = form.body.data.strip()

    if form.cover_image.data:
        old_cover = story.cover_image
        story.cover_image = _save_story_image(form.cover_image.data)
        _delete_story_image(old_cover)


@heritage_bp.route("/")
def index():
    # Stage 5 adds real heritage articles.
    return render_template("heritage/index.html")


@heritage_bp.route("/blogs")
def blogs():
    query = Story.query.filter_by(status="approved")

    page = request.args.get("page", 1, type=int)
    listings = query.order_by(Story.created_at.desc()).paginate(page=page, per_page=12)

    return render_template("heritage/blogs.html", listings=listings)


@heritage_bp.route("/stories/mine")
@login_required
def my_stories():
    listings = (
        Story.query.filter_by(author_id=current_user.id).order_by(Story.created_at.desc()).all()
    )
    return render_template("heritage/my_stories.html", listings=listings)


@heritage_bp.route("/stories/add", methods=["GET", "POST"])
@login_required
def add_story():
    form = StoryForm()

    if form.validate_on_submit():
        story = Story(
            author_id=current_user.id,
            slug=unique_slug(form.title.data.strip()),
            status="pending",
        )
        _apply_form_to_story(form, story)
        db.session.add(story)
        db.session.commit()
        flash(
            "Thanks for sharing! Your story has been submitted and is awaiting admin approval.",
            "success",
        )
        return redirect(url_for("heritage.my_stories"))

    return render_template("heritage/story_add.html", form=form)


@heritage_bp.route("/stories/<slug>/edit", methods=["GET", "POST"])
@login_required
def edit_story(slug):
    story = Story.query.filter_by(slug=slug).first_or_404()
    if story.author_id != current_user.id and not current_user.is_admin:
        abort(403)

    form = StoryForm(obj=story)
    if form.validate_on_submit():
        _apply_form_to_story(form, story)
        db.session.commit()
        flash("Your story has been updated.", "success")
        return redirect(url_for("heritage.my_stories"))

    return render_template("heritage/story_edit.html", form=form, story=story)


@heritage_bp.route("/stories/<slug>")
def story_detail(slug):
    story = Story.query.filter_by(slug=slug).first_or_404()

    is_author = current_user.is_authenticated and story.author_id == current_user.id
    is_admin = current_user.is_authenticated and current_user.is_admin
    if story.status != "approved" and not (is_author or is_admin):
        abort(404)

    return render_template("heritage/story_detail.html", story=story)


@heritage_bp.route("/cuisine")
def cuisine():
    # Stage 5 adds real recipe articles; this page already carries a
    # real Wikipedia summary rather than lorem-ipsum placeholder text.
    return render_template("heritage/cuisine.html")
