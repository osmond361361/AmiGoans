from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Email, Length


class NewsletterForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=255)])
