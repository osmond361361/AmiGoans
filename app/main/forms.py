from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import URL, DataRequired, Email, Length, Optional


class NewsletterForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=255)])


class IdeaForm(FlaskForm):
    title = StringField("Summary", validators=[DataRequired(), Length(min=2, max=150)])
    description = TextAreaField(
        "Tell us more", validators=[DataRequired(), Length(min=10, max=4000)]
    )


class IssueForm(FlaskForm):
    description = TextAreaField(
        "What went wrong?", validators=[DataRequired(), Length(min=10, max=4000)]
    )
    page_url = StringField(
        "Page or link (optional)", validators=[Optional(), URL(), Length(max=500)]
    )
