from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.models.village_landmark import CATEGORIES

LANDMARK_CATEGORY_LABELS = {
    "church": "Church",
    "temple": "Temple",
    "mosque": "Mosque",
    "school": "School",
    "other": "Other landmark",
}


class VillageLandmarkForm(FlaskForm):
    category = SelectField("Type", choices=[(c, LANDMARK_CATEGORY_LABELS[c]) for c in CATEGORIES])
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=150)])
    description = TextAreaField("Description (optional)", validators=[Optional(), Length(max=2000)])


class VillagePhotoForm(FlaskForm):
    caption = StringField("Caption", validators=[DataRequired(), Length(min=2, max=255)])
    image = FileField(
        "Photo", validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only (JPG or PNG).")]
    )
