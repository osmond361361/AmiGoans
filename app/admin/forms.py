from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.models.feedback import STATUSES as FEEDBACK_STATUSES


class PageForm(FlaskForm):
    title = StringField("Page Title", validators=[DataRequired(), Length(min=2, max=150)])
    content_html = TextAreaField("Content (HTML)", validators=[DataRequired()])


class FeedbackResponseForm(FlaskForm):
    status = SelectField(
        "Status", choices=[(s, s.replace("_", " ").capitalize()) for s in FEEDBACK_STATUSES]
    )
    admin_response = TextAreaField(
        "Response (emailed to the submitter if sent)",
        validators=[Optional(), Length(max=4000)],
    )
