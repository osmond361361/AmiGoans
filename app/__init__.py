from datetime import datetime, timezone

from flask import Flask, render_template

from app.extensions import csrf, db, login_manager, migrate
from config import config


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    register_blueprints(app)
    register_error_handlers(app)
    register_context_processors(app)
    register_login_manager(app)

    return app


def register_context_processors(app):
    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.now(timezone.utc).year}


def register_login_manager(app):
    # Stage 2 introduces the User model; this stub keeps Flask-Login
    # functional (it requires a user_loader) until real users exist.
    @login_manager.user_loader
    def load_user(user_id):
        return None


def register_blueprints(app):
    from app.admin import admin_bp
    from app.auth import auth_bp
    from app.businesses import businesses_bp
    from app.events import events_bp
    from app.heritage import heritage_bp
    from app.jobs import jobs_bp
    from app.main import main_bp
    from app.members import members_bp
    from app.videos import videos_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(members_bp, url_prefix="/members")
    app.register_blueprint(businesses_bp, url_prefix="/businesses")
    app.register_blueprint(events_bp, url_prefix="/events")
    app.register_blueprint(heritage_bp, url_prefix="/heritage")
    app.register_blueprint(videos_bp, url_prefix="/tv")
    app.register_blueprint(jobs_bp, url_prefix="/jobs")
    app.register_blueprint(admin_bp, url_prefix="/admin")


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500
