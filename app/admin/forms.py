from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length


class PageForm(FlaskForm):
    title = StringField("Page Title", validators=[DataRequired(), Length(min=2, max=150)])
    content_html = TextAreaField("Content (HTML)", validators=[DataRequired()])
