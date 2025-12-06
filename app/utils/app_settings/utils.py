from flask import request, current_app
from typing import List
from cachetools import cached, TTLCache

from app.extensions import db
from app.enums.payments import PaymentMethods
from app.enums.settings import GeneralSettingsKeys, PaymentMethodSettingKeys
from app.models.settings import GeneralSetting, PaymentMethodSettings
from app.logging import log_event, log_error


def get_default_setting(key: GeneralSettingsKeys) -> str:
    """
    Retrieves the default value for a given settings key.

    Args:
        key (GeneralSettingsKeys): The settings key Enum.

    Returns:
        str: The default value for the setting, or an empty string if not explicitly defined.
    """
    
    from flask import current_app, has_request_context, request
    
    # Get the current domain
    if has_request_context():
        current_domain = request.host_url.rstrip('/')
    else:
        # Fallback to configured domain or localhost
        server_name = current_app.config.get('SERVER_NAME', 'localhost:5000')
        scheme = current_app.config.get('PREFERRED_URL_SCHEME', 'http')
        current_domain = f"{scheme}://{server_name}"
    
    
    log_event("current_domain", current_domain)
    
    defaults = {
        GeneralSettingsKeys.SITE_TITLE: "eSim App",
        GeneralSettingsKeys.TIMEZONE: "UTC",
        
        GeneralSettingsKeys.PLATFORM_URL: current_domain,  # Where your application files live
        GeneralSettingsKeys.SITE_URL: current_domain,      # Where your site is accessed by users
        
        GeneralSettingsKeys.CURRENCY: "USD",
        GeneralSettingsKeys.NUMBER_OF_DECIMALS: "2",
        GeneralSettingsKeys.CURRENCY_POSITION: "left",
        GeneralSettingsKeys.THOUSAND_SEPARATOR: ",",
        GeneralSettingsKeys.DECIMAL_SEPARATOR: ".",
    }
    return defaults.get(key, "")  # Default to empty string


def get_all_general_settings() -> dict[str, str]:
    """
    Retrieves all general settings as a dictionary. {key: value}

    Returns:
        dict[str, str]: A dictionary where the keys are setting names and values are their stored values.
    """
    general_settings: list[GeneralSetting] = GeneralSetting.query.all()
    
    return {setting.key: setting.value for setting in general_settings}


# Create a cache with a Time-To-Live (TTL) of 12 hour (43200 seconds)
cache = TTLCache(maxsize=100, ttl=18000)

@cached(cache) # Cache settings to optimize performance
def get_general_setting(key: GeneralSettingsKeys, default=None) -> str | None:
    """
    Retrieves a specific general setting value from the database.

    Args:
        key (GeneralSettingsKeys): The settings key Enum.
        default: Default value if setting is not found.

    Returns:
        str: The stored setting value, or default.
    """
    
    setting: GeneralSetting = GeneralSetting.query.filter_by(key=str(key)).first()
    
    return setting.value if setting and setting.value else default

def save_general_setting(key: GeneralSettingsKeys, value: str):
    """
    Saves or updates a specific setting in the database.

    Args:
        key (GeneralSettingsKeys): The settings key Enum.
        value (str): The value to store.
    """
    setting: GeneralSetting = GeneralSetting.query.filter_by(key=str(key)).first()
    log_event("setting", setting)
    
    if setting:
        setting.value = value
        db.session.merge(setting)
    else:
        setting = GeneralSetting(key=key, value=value)
        db.session.merge(setting)
        db.session.add(setting)
    
    
    db.session.commit()
    get_general_setting.cache_clear()  # Clears cache to reflect new values

def get_currency_settings() -> tuple:
    """Get all currency-related settings."""
    return (
        get_general_setting( GeneralSettingsKeys.CURRENCY, 'USD' ), # currency_code

        get_general_setting( GeneralSettingsKeys.NUMBER_OF_DECIMALS, '2' ), # decimal_places

        get_general_setting( GeneralSettingsKeys.CURRENCY_POSITION, 'left' ),

        get_general_setting( GeneralSettingsKeys.THOUSAND_SEPARATOR, ','),

        get_general_setting( GeneralSettingsKeys.DECIMAL_SEPARATOR, '.'),

    )

def get_payment_method_settings(method: PaymentMethods) -> dict:
    """
    Retrieve all settings for a specific payment method.

    Args:
        method (PaymentMethods): The payment method key.

    Returns:
        dict: A dictionary of all settings for the method.
    """
    settings: PaymentMethodSettings = PaymentMethodSettings.query.filter_by(method=str(method)).all()
    return {setting.key: setting.value for setting in settings}


def get_payment_method_setting(method: PaymentMethods, key: PaymentMethodSettingKeys) -> str | None:
    """
    Retrieve a specific payment method setting.

    Args:
        method (PaymentMethods): The payment method key (e.g., 'bacs', 'cod', 'gateway').
        key (PaymentMethodSettingKeys): The setting key (e.g., 'enabled', 'account_number').

    Returns:
        str: The setting value, or None if not found.
    """
    setting: PaymentMethodSettings = PaymentMethodSettings.query.filter_by(method=str(method), key=str(key)).first()
    return setting.value if setting else None

def save_payment_method_setting(method: PaymentMethods, key: PaymentMethodSettingKeys, value: str):
    """
    Save or update a payment setting.

    Args:
        method (PaymentMethods): The payment method key.
        key (PaymentMethodSettingKeys): The setting key.
        value (str): The value to store.
    """
    setting: PaymentMethodSettings = PaymentMethodSettings.query.filter_by(method=str(method), key=str(key)).first()
    
    if setting:
        setting.value = value
    else:
        setting = PaymentMethodSettings(method=str(method), key=str(key), value=value)
        db.session.add(setting)
    
    db.session.commit()


def get_default_payment_method_settings() -> dict[PaymentMethods, dict[PaymentMethodSettingKeys, str]]:
    """
    Returns a dictionary of default payment method settings.

    Returns:
        dict: {PaymentMethods: {PaymentMethodSettingKeys: Default Value}}
    """
    DEFAULT_PAYMENT_SETTINGS = {
        PaymentMethods.BACS: {
            PaymentMethodSettingKeys.ENABLED: "false",
            PaymentMethodSettingKeys.TITLE: "Direct Bank Transfer",
            PaymentMethodSettingKeys.DESCRIPTION: "Make your payment directly into our bank account. Please use your Order ID as the payment reference. Your order will not be shipped until the funds have cleared in our account.",
            PaymentMethodSettingKeys.ACCOUNT_NAME: "",
            PaymentMethodSettingKeys.ACCOUNT_NUMBER: "",
            PaymentMethodSettingKeys.BANK_NAME: "",
            PaymentMethodSettingKeys.SORT_CODE: "",
            PaymentMethodSettingKeys.IBAN: "",
            PaymentMethodSettingKeys.BIC_SWIFT: "",
        },
        PaymentMethods.CHECK: {
            PaymentMethodSettingKeys.ENABLED: "false",
            PaymentMethodSettingKeys.TITLE: "Check Payments",
            PaymentMethodSettingKeys.DESCRIPTION: "Please send a check to Store Name, Store Street, Store Town, Store State / County, Store Postcode.",
        },
        PaymentMethods.COD: {
            PaymentMethodSettingKeys.ENABLED: "false",
            PaymentMethodSettingKeys.TITLE: "Cash on Delivery",
            PaymentMethodSettingKeys.DESCRIPTION: "Pay with cash upon delivery.",
            PaymentMethodSettingKeys.ENABLE_FOR_SHIPPING: "",
            PaymentMethodSettingKeys.ACCEPT_VIRTUAL_ORDERS: "false",
        },
        PaymentMethods.GATEWAY: {
            PaymentMethodSettingKeys.ENABLED: "true",
            PaymentMethodSettingKeys.PROVIDER: "flutterwave",
            PaymentMethodSettingKeys.BITPAY_API_KEY: "",
            PaymentMethodSettingKeys.FLUTTERWAVE_API_KEY: "",
            PaymentMethodSettingKeys.PAYSTACK_API_KEY: "",
        },
    }
    
    return DEFAULT_PAYMENT_SETTINGS


def get_active_payment_gateway() -> dict:
    """
    Retrieves the currently active payment gateway and its credentials.

    Returns:
        dict: Contains 'provider' and relevant credentials.
    """
    
    fallback = {
        "provider": current_app.config.get("PAYMENT_GATEWAY"),
        "credentials": {
            "api_key": current_app.config.get("PAYMENT_GATEWAY_API_KEY"),
            "secret_key": current_app.config.get("PAYMENT_GATEWAY_SECRET_KEY"),
            "public_key": current_app.config.get("PAYMENT_GATEWAY_PUBLIC_KEY"),
            "test_mode": current_app.config.get("PAYMENT_GATEWAY_TEST_MODE"),
            "test_api_key": current_app.config.get("PAYMENT_GATEWAY_TEST_API_KEY"),
            "test_secret_key": current_app.config.get("PAYMENT_GATEWAY_TEST_SECRET_KEY"),
            "test_public_key": current_app.config.get("PAYMENT_GATEWAY_TEST_PUBLIC_KEY")
        }
    }
    
    provider_settings = get_payment_method_settings(PaymentMethods.GATEWAY)
    provider = provider_settings.get("provider", "").lower()  # Force lowercase
    
    if provider:
    
        provider_data = {
            key: value for key, value in provider_settings.items() 
            if key.startswith(provider) or key == "provider"
        }
        
        # Create the credentials dictionary
        credentials = {
            key.replace(f"{provider}_", ""): value  # Remove provider prefix
            for key, value in provider_data.items() 
            if key.startswith(provider)  # Only include keys starting with the provider
        }
        return {"provider": provider, "credentials": credentials}
    else:
        return fallback


def get_platform_url() -> str:
    """Return the platform base URL used for redirects in payment flows."""
    return current_app.config.get("APP_DOMAIN", "http://localhost:3000")