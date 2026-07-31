from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import URL, DataRequired, Length, Optional


class JobForm(FlaskForm):
    title = StringField("Job Title", validators=[DataRequired(), Length(min=2, max=150)])
    location = StringField("Location", validators=[DataRequired(), Length(max=150)])
    job_url = StringField("Job Link", validators=[DataRequired(), URL(), Length(max=500)])
    description = TextAreaField(
        "Additional Details (optional)", validators=[Optional(), Length(max=4000)]
    )
