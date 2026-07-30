from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import SelectField, StringField, TextAreaField
from wtforms.validators import URL, DataRequired, Email, Length, Optional, Regexp

from app.models.business import CATEGORIES

PHONE_REGEXP = r"^\+?[0-9 ]{7,20}$"
NATIONS = ("England", "Scotland", "Wales", "Northern Ireland")


class BusinessForm(FlaskForm):
    name = StringField("Business Name", validators=[DataRequired(), Length(min=2, max=150)])
    description = TextAreaField(
        "Description", validators=[DataRequired(), Length(min=20, max=4000)]
    )
    category = SelectField(
        "Category", choices=[(c, c) for c in CATEGORIES], validators=[DataRequired()]
    )

    telephone = StringField(
        "Telephone",
        validators=[Optional(), Regexp(PHONE_REGEXP, message="Enter a valid phone number.")],
    )
    whatsapp = StringField(
        "WhatsApp",
        validators=[Optional(), Regexp(PHONE_REGEXP, message="Enter a valid phone number.")],
    )
    email = StringField("Business Email", validators=[Optional(), Email(), Length(max=255)])
    website = StringField("Website", validators=[Optional(), URL(), Length(max=255)])
    facebook_url = StringField("Facebook Page", validators=[Optional(), URL(), Length(max=255)])

    town = StringField("Town / City", validators=[DataRequired(), Length(max=100)])
    county = StringField("County", validators=[Optional(), Length(max=100)])
    nation = SelectField("Nation", choices=[(n, n) for n in NATIONS], validators=[DataRequired()])
    postcode_district = StringField(
        "Postcode District",
        validators=[Optional(), Length(max=10)],
        description="e.g. SW1A - just the outward part, not your full postcode.",
    )

    logo = FileField(
        "Logo", validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only (JPG or PNG).")]
    )
    cover_image = FileField(
        "Cover Photo", validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only (JPG or PNG).")]
    )
