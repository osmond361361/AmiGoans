from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, StringField
from wtforms.validators import DataRequired, Length, Optional, Regexp

PHONE_REGEXP = r"^\+?[0-9 ]{7,20}$"


class ProfileForm(FlaskForm):
    display_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=100)])
    phone_number = StringField(
        "Mobile Number",
        validators=[
            Optional(),
            Regexp(PHONE_REGEXP, message="Enter a valid phone number, e.g. 07700 900123."),
            Length(max=30),
        ],
    )
    sms_marketing_consent = BooleanField(
        "I'd like to receive occasional offers from Ami Goans and its advertisers by SMS"
    )
    photo = FileField(
        "Profile Photo",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only (JPG or PNG).")],
    )
