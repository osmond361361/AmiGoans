from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length


class StoryForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=2, max=150)])
    body = TextAreaField("Your Story", validators=[DataRequired(), Length(min=50, max=8000)])
    cover_image = FileField(
        "Photo (optional)",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only (JPG or PNG).")],
    )
