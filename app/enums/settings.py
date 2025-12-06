from enum import Enum


class GeneralSettingsKeys(Enum):
    """
    Enumeration of predefined settings keys to maintain consistency and prevent typos.
    """
    SITE_TITLE = "site_title"
    TAGLINE = "tagline"
    ADMIN_EMAIL = "admin_email"
    TIMEZONE = "timezone"
    WEEK_STARTS_ON = "week_starts_on"
    
    PLATFORM_URL = "platform_url"
    SITE_URL = "site_url"
    
    # Currency Settings
    CURRENCY = "currency"
    CURRENCY_POSITION = "currency_position"
    THOUSAND_SEPARATOR = "thousand_separator"
    DECIMAL_SEPARATOR = "decimal_separator"
    NUMBER_OF_DECIMALS = "number_of_decimals"
    
    def __str__(self):
        """
        Returns the string representation of the Enum value.

        Returns:
            str: The key as a string.
        """
        return self.value  # Allows direct use without .value


class PaymentMethodSettingKeys(Enum):
    """
    Enum representing keys for payment method settings.
    Ensures consistency and prevents typos.
    """
    ENABLED = "enabled"
    TITLE = "title"
    DESCRIPTION = "description"

    # BACS-specific settings
    ACCOUNT_NAME = "account_name"
    ACCOUNT_NUMBER = "account_number"
    BANK_NAME = "bank_name"
    SORT_CODE = "sort_code"
    IBAN = "iban"
    BIC_SWIFT = "bic_swift"

    # COD-specific settings
    ENABLE_FOR_SHIPPING = "enable_for_shipping"
    ACCEPT_VIRTUAL_ORDERS = "accept_virtual_orders"

    # Gateway settings
    PROVIDER = "provider"
    BITPAY_API_KEY = "bitpay_api_key"
    
    FLUTTERWAVE_API_KEY = "flutterwave_api_key"
    FLUTTERWAVE_SECRET_KEY = "flutterwave_secret_key"
    FLUTTERWAVE_TEST_SECRET_KEY = "flutterwave_test_secret_key"
    FLUTTERWAVE_PUBLIC_KEY = "flutterwave_public_key"
    FLUTTERWAVE_TEST_PUBLIC_KEY = "flutterwave_test_public_key"
    FLUTTERWAVE_SECRET_HASH = "flutterwave_secret_hash"
    
    PAYSTACK_API_KEY = "paystack_api_key"
    PAYSTACK_SECRET_KEY = "paystack_secret_key"
    PAYSTACK_TEST_SECRET_KEY = "paystack_test_secret_key"
    PAYSTACK_PUBLIC_KEY = "paystack_public_key"
    PAYSTACK_TEST_PUBLIC_KEY = "paystack_test_public_key"

    def __str__(self):
        return self.value  # Ensures usage as strings in queries
