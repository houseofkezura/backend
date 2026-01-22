"""
Author: Emmanuel Olowu
Link: https://github.com/zeddyemy
Copyright: © 2024 Emmanuel Olowu <zeddyemy@gmail.com>
License: GNU, see LICENSE for more details.
"""
from wsgiref.validate import validator
from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, TextAreaField, SelectField, BooleanField, HiddenField, SelectMultipleField, SubmitField, ValidationError, widgets)
from wtforms.validators import InputRequired, DataRequired, EqualTo, Length, Optional, Email, Regexp, URL
from flask_wtf.file import FileField, FileAllowed
import pycountry

from app.models.settings import PaymentGateway
from app.enums.payments import PaymentGatewayName
from app.logging import log_event, log_error
from app.utils.constants.currencies import CURRENCY_SYMBOLS

def get_day_choices(include_default: bool = True) -> list[tuple[str, str]]:
    """
    Return a list of (id, name) tuples for days of the week.
    
    If `include_default` is True, prepend ("", "— Select day —").
    """
    days = [
        ("0", "Sunday"),
        ("1", "Monday"),
        ("2", "Tuesday"),
        ("3", "Wednesday"),
        ("4", "Thursday"),
        ("5", "Friday"),
        ("6", "Saturday"),
    ]
    
    choices = [("", "— Select day —")] + days if include_default else days

    return choices


class GeneralSettingsForm(FlaskForm):
    site_title = StringField('Site Title', validators=[InputRequired()])
    tagline = StringField('Tagline', validators=[], description="In a few words, explain what this site is about. Example: “Just another E-Commerce site.”")
    
    platform_url = StringField(
        'Platform Address (URL)',
        validators=[DataRequired(), URL()],
        description="The URL where your StoreZed application files are installed.",
    )
    site_url = StringField(
        'Site Address (URL)',
        validators=[DataRequired(), URL()],
        description="Enter the same address here unless you want your site home page to be different from the StoreZed installation directory."
    )
    
    admin_email = StringField('Administration Email Address', description="This address is used for admin purposes. If you change this, an email will be sent to your new address to confirm it. The new address will not become active until confirmed.")
    timezone = StringField('Timezone')
    week_starts_on = SelectField('Week Starts On', choices=[], coerce=int, validate_choice=False)
    
    # Currency Settings
    currency = SelectField( "Currency", validators=[InputRequired()], description="This controls what currency prices are listed at in the catalog and which currency gateways will take payments in.")
    
    currency_position = SelectField("Currency Position", choices=[
        ("left", "Left ($100)"),
        ("right", "Right (100$)"),
        ("left_space", "Left with space ($ 100)"),
        ("right_space", "Right with space (100 $)")
    ], validators=[InputRequired()], description="This controls the position of the currency symbol.")
    thousand_separator = StringField("Thousand Separator", description="This sets the thousand separator of displayed prices.")
    decimal_separator = StringField("Decimal Separator", description="This sets the decimal separator of displayed prices.")
    number_of_decimals = SelectField(
        "Number of Decimals",
        choices=[(str(i), str(i)) for i in range(0, 4)],
        validators=[InputRequired()],
        description="This sets the number of decimal points shown in displayed prices."
    )
    
    submit = SubmitField('Save Changes')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.week_starts_on.choices = get_day_choices(False)
        self.currency.choices = [
            ( currency.alpha_3, currency.name + " (" + CURRENCY_SYMBOLS.get(currency.alpha_3, "") + ") — " + currency.alpha_3 )
            for currency in sorted(pycountry.currencies, key=lambda c: c.name)
        ]
    

