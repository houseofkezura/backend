"""
Settings helper shims.

This module centralizes access to platform settings that would typically be
stored in a database or environment variables. For now, it provides minimal
helpers used by payments. Later, these can be wired to real persistence.
"""

from __future__ import annotations

from typing import Any, Optional
from flask import current_app


def get_general_setting(key: str, default: Any | None = None) -> Any:
    """Fetch a general platform setting, falling back to app config or default."""
    return current_app.config.get(key, default)


def get_active_payment_gateway() -> Optional[dict]:
    """
    Return the active payment gateway configuration.

    Expected structure:
    {
        "provider": "flutterwave" | "paystack" | "bitpay",
        "credentials": {
            "api_key": "...",
            "secret_key": "...",
            "public_key": "...",
            "test_mode": "true" | "false",
            "test_api_key": "...",
            "test_secret_key": "...",
            "test_public_key": "..."
        }
    }
    """
    return {
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


def get_platform_url() -> str:
    """Return the platform base URL used for redirects in payment flows."""
    return current_app.config.get("APP_DOMAIN", "http://localhost:3000")

