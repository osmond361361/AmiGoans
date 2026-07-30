from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
oauth = OAuth()
mail = Mail()

login_manager.login_view = "auth.sign_in"
login_manager.login_message_category = "info"
