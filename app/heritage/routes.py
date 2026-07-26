from flask import render_template

from app.heritage import heritage_bp


@heritage_bp.route("/")
def index():
    # Stage 5 adds real heritage articles.
    return render_template("heritage/index.html")


@heritage_bp.route("/blogs")
def blogs():
    # Stage 5 adds real blog posts.
    return render_template("heritage/blogs.html")


@heritage_bp.route("/cuisine")
def cuisine():
    # Stage 5 adds real recipe articles; this page already carries a
    # real Wikipedia summary rather than lorem-ipsum placeholder text.
    return render_template("heritage/cuisine.html")
