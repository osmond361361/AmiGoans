from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth import auth_bp
from app.auth.forms import JoinForm, SignInForm
from app.extensions import db, oauth
from app.models import User


@auth_bp.route("/join", methods=["GET", "POST"])
def join():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = JoinForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists. Try signing in instead.", "warning")
            return render_template("auth/join.html", form=form)

        user = User(display_name=form.display_name.data.strip(), email=email)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Welcome to Ami Goans! Your account has been created.", "success")
        return redirect(url_for("main.home"))

    return render_template("auth/join.html", form=form)


@auth_bp.route("/sign-in", methods=["GET", "POST"])
def sign_in():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = SignInForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(form.password.data):
            flash("Incorrect email or password.", "danger")
            return render_template("auth/sign_in.html", form=form)

        login_user(user, remember=form.remember_me.data)
        flash(f"Welcome back, {user.display_name}!", "success")

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return redirect(url_for("main.home"))

    return render_template("auth/sign_in.html", form=form)


@auth_bp.route("/sign-out")
@login_required
def sign_out():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.home"))


def find_or_create_oauth_user(provider, provider_id, email, display_name):
    user = User.query.filter_by(oauth_provider=provider, oauth_id=provider_id).first()
    if user:
        return user

    # An account with this email already exists (e.g. created with a
    # password) - link this provider to it rather than erroring.
    user = User.query.filter_by(email=email).first()
    if user:
        user.oauth_provider = provider
        user.oauth_id = provider_id
        db.session.commit()
        return user

    user = User(
        email=email,
        display_name=display_name,
        oauth_provider=provider,
        oauth_id=provider_id,
    )
    db.session.add(user)
    db.session.commit()
    return user


@auth_bp.route("/google")
def google_login():
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        return render_template("auth/provider_not_configured.html", provider="Google")

    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo")

    if not userinfo or not userinfo.get("email"):
        flash("Google sign-in did not share an email address. Please try another method.", "danger")
        return redirect(url_for("auth.sign_in"))

    user = find_or_create_oauth_user(
        provider="google",
        provider_id=userinfo["sub"],
        email=userinfo["email"].lower().strip(),
        display_name=userinfo.get("name") or userinfo["email"],
    )
    login_user(user)
    flash(f"Welcome, {user.display_name}!", "success")
    return redirect(url_for("main.home"))


@auth_bp.route("/facebook")
def facebook_login():
    if not current_app.config.get("FACEBOOK_CLIENT_ID"):
        return render_template("auth/provider_not_configured.html", provider="Facebook")

    redirect_uri = url_for("auth.facebook_callback", _external=True)
    return oauth.facebook.authorize_redirect(redirect_uri)


@auth_bp.route("/facebook/callback")
def facebook_callback():
    token = oauth.facebook.authorize_access_token()
    profile = oauth.facebook.get("me?fields=id,name,email", token=token).json()

    if not profile.get("email"):
        flash(
            "Facebook sign-in did not share an email address. Please try another method.",
            "danger",
        )
        return redirect(url_for("auth.sign_in"))

    user = find_or_create_oauth_user(
        provider="facebook",
        provider_id=profile["id"],
        email=profile["email"].lower().strip(),
        display_name=profile.get("name") or profile["email"],
    )
    login_user(user)
    flash(f"Welcome, {user.display_name}!", "success")
    return redirect(url_for("main.home"))
