"""
Author: Emmanuel Olowu
Link: https://github.com/zeddyemy
Copyright: © 2024 Emmanuel Olowu <zeddyemy@gmail.com>
License: GNU, see LICENSE for more details.
"""
from wsgiref.validate import validator
from flask_wtf import FlaskForm
from wtforms import (StringField, BooleanField, IntegerField, TextAreaField, SelectField, HiddenField, SelectMultipleField, SubmitField, ValidationError, widgets)
from wtforms.validators import InputRequired, DataRequired, EqualTo, Length, Optional, Email, Regexp
from flask_wtf.file import FileField, FileAllowed

from app.models.settings import PaymentMethodSettings, PaymentGateway
from app.enums.payments import PaymentMethods, PaymentGatewayName
from app.utils.app_settings.utils import get_payment_method_settings
from app.utils.payments.utils import get_payment_providers


class BasePaymentMethodForm(FlaskForm):
    """
    Base form containing common fields for all payment methods.
    """
    enabled = BooleanField("Enable / Disable", default=False)
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()], description="Displays to customers when they’re choosing a payment method.")
    submit = SubmitField("Save Settings")
    
    def __init__(self, *args, **kwargs):
        """
        Override constructor to ensure boolean fields are correctly processed.
        """
        # Convert string-based boolean fields to actual boolean values
        for field in ["enabled"]:
            if field in kwargs and isinstance(kwargs[field], str):
                kwargs[field] = kwargs[field].lower() == "true"

        super().__init__(*args, **kwargs)

class BacsPaymentForm(BasePaymentMethodForm):
    """
    Form for configuring Direct Bank Transfer (BACS) settings.
    """
    instructions = TextAreaField('Instructions', validators=[Optional()], description="Displays to customers after they place an order with this payment method.")
    account_name = StringField("Account Name", validators=[DataRequired()])
    account_number = StringField("Account Number", validators=[DataRequired()])
    bank_name = StringField("Bank Name", validators=[DataRequired()])
    sort_code = StringField("Sort Code", validators=[Optional()])
    iban = StringField("IBAN", validators=[Optional()])
    bic_swift = StringField("BIC / Swift", validators=[Optional()])
    

class CheckPaymentForm(BasePaymentMethodForm):
    """
    Form for configuring Check Payments settings.
    """
    instructions = TextAreaField("Instructions for Customers", validators=[Optional()], description="Displays to customers after they place an order with this payment method.")

class CodPaymentForm(BasePaymentMethodForm):
    """
    Form for configuring Cash on Delivery (COD) settings.
    """
    enable_for_shipping = SelectField("Enable for Shipping Methods", choices=[], validators=[Optional()])
    accept_virtual_orders = BooleanField("Accept for Virtual Orders", default=False)
    
    def __init__(self, *args, **kwargs):
        """
        Handle boolean conversion for 'accept_virtual_orders'.
        """
        if "accept_virtual_orders" in kwargs and isinstance(kwargs["accept_virtual_orders"], str):
            kwargs["accept_virtual_orders"] = kwargs["accept_virtual_orders"].lower() == "true"
        
        super().__init__(*args, **kwargs)


def get_provider_form_choices() -> list[tuple]:
    provider_form_choices = []
    for provider in get_payment_providers():
        provider_form_choices.append((provider.lower(), provider.title()))
    
    return provider_form_choices

class GatewayPaymentForm(BasePaymentMethodForm):
    """
    Form for configuring Payment Gateway Providers settings.
    """
    provider = SelectField("Select Payment Provider", choices=get_provider_form_choices(), validators=[DataRequired()], description=f"These providers provide merchants with the tools and services needed to accept online payments from local and international customers using Crypto, Mastercard, Visa, Verve Cards and Bank Accounts. Sign up for an account on either platforms, and get your API keys.")
    
    bitpay_test_mode = BooleanField("Enable Test Mode", default=True)
    bitpay_api_key = StringField("BitPay API Key", validators=[Optional()])
    bitpay_test_api_key = StringField("BitPay Test API Key", validators=[Optional()])
    bitpay_secret_key = StringField("BitPay Secret Key", validators=[Optional()])
    
    flutterwave_test_mode = BooleanField("Enable Test Mode", default=True)
    flutterwave_api_key = StringField("Flutterwave API Key", validators=[Optional()])
    flutterwave_secret_key = StringField("Flutterwave Secret Key", validators=[Optional()])
    flutterwave_test_secret_key = StringField("Flutterwave Test Secret Key", validators=[Optional()])
    flutterwave_public_key = StringField("Flutterwave Public Key", validators=[Optional()])
    flutterwave_test_public_key = StringField("Flutterwave Test Public Key", validators=[Optional()])
    
    paystack_test_mode = BooleanField("Enable Test Mode", default=True)
    paystack_api_key = StringField("Paystack API Key", validators=[Optional()])
    paystack_secret_key = StringField("Paystack Secret Key", validators=[Optional()])
    paystack_test_secret_key = StringField("Paystack Test Secret Key", validators=[Optional()])
    paystack_public_key = StringField("Paystack Public Key", validators=[Optional()])
    paystack_test_public_key = StringField("Paystack Test Public Key", validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        """
        Handle boolean conversion for 'bitpay_test_mode'.
        """
        if "bitpay_test_mode" in kwargs and isinstance(kwargs["bitpay_test_mode"], str):
            kwargs["bitpay_test_mode"] = kwargs["bitpay_test_mode"].lower() == "true"
        
        if "flutterwave_test_mode" in kwargs and isinstance(kwargs["flutterwave_test_mode"], str):
            kwargs["flutterwave_test_mode"] = kwargs["flutterwave_test_mode"].lower() == "true"
        
        if "paystack_test_mode" in kwargs and isinstance(kwargs["paystack_test_mode"], str):
            kwargs["paystack_test_mode"] = kwargs["paystack_test_mode"].lower() == "true"
        
        super().__init__(*args, **kwargs)



def get_payment_method_forms() -> dict[PaymentMethods, BacsPaymentForm | CheckPaymentForm | CodPaymentForm | GatewayPaymentForm]:
    # Map PaymentMethods Enum to their respective forms
    PAYMENT_FORMS = {
        PaymentMethods.BACS: BacsPaymentForm,
        PaymentMethods.CHECK: CheckPaymentForm,
        PaymentMethods.COD: CodPaymentForm,
        PaymentMethods.GATEWAY: GatewayPaymentForm
    }
    
    return PAYMENT_FORMS

