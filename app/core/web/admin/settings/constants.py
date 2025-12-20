from flask import url_for
from app.enums import PaymentMethods # Import the Enum for consistency

GATEWAY_REQUIRED_FIELDS = {
    "bitpay": ["bitpay_api_key"],
    "flutterwave": ["flutterwave_api_key", "flutterwave_merchant_id"],
    "paystack": ["paystack_api_key", "paystack_secret_key"],
    "stripe": ["stripe_public_key", "stripe_secret_key", "stripe_webhook_secret"],  # Example of Stripe requiring extra fields
    "coinbase": ["coinbase_api_key", "coinbase_webhook_secret"]
}

PAYMENT_METHOD_OVERVIEW = [
    {
        "key": PaymentMethods.GATEWAY.value,
        "title": "Payment Gateway Providers",
        "description": "Accept payments via third-party providers like BitPay, Flutterwave, or Paystack.",
        "enabled_key": "payment_gateway_enabled",
        "setup_url": lambda: url_for("web_admin.payment_setup", method=PaymentMethods.GATEWAY.value),
    },
    {
        "key": PaymentMethods.BACS.value,
        "title": "Direct Bank Transfer (BACS)",
        "description": "Accept payments in person via BACS. More commonly known as direct bank/wire transfer.",
        "enabled_key": "payment_bacs_enabled",
        "setup_url": lambda: url_for("web_admin.payment_setup", method=PaymentMethods.BACS.value),
    },
    {
        "key": PaymentMethods.CHECK.value,
        "title": "Check Payments",
        "description": "Accept payments via mailed checks.",
        "enabled_key": "payment_check_enabled",
        "setup_url": lambda: url_for("web_admin.payment_setup", method=PaymentMethods.CHECK.value),
    },
    {
        "key": PaymentMethods.COD.value,
        "title": "Cash on Delivery (COD)",
        "description": "Allow your customers to pay with cash (or by other means) on delivery.",
        "enabled_key": "payment_cod_enabled",
        "setup_url": lambda: url_for("web_admin.payment_setup", method=PaymentMethods.COD.value),
    },
]