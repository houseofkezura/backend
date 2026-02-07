"""
Website/site helpers.

Small shims to provide URLs for the platform and individual sites.
"""

from __future__ import annotations

from flask import current_app


def get_site_url() -> str:
    """Return the current site base URL. For now, mirror platform URL."""
    return current_app.config.get("APP_DOMAIN", "http://localhost:5173")


def get_platform_url() -> str:
    """Alias for platform URL used in multiple modules."""
    return current_app.config.get("APP_DOMAIN", "http://localhost:5173")

