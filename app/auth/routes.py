from flask import render_template

from app.auth import auth_bp


@auth_bp.route("/sign-in")
def sign_in():
    # Stage 3 adds real authentication. This is the visual shell only.
    return render_template("auth/sign_in.html")


@auth_bp.route("/join")
def join():
    # Stage 3 adds real registration. This is the visual shell only.
    return render_template("auth/join.html")


@auth_bp.route("/google")
def google_placeholder():
    return render_template("auth/provider_not_configured.html", provider="Google")


@auth_bp.route("/facebook")
def facebook_placeholder():
    return render_template("auth/provider_not_configured.html", provider="Facebook")
