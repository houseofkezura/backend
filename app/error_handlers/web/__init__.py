"""
Reusable error handler attachment for web blueprints (admin UI).

Attaches common handlers (HTTP, DB, unexpected) to a given blueprint so
web routes return HTML error pages or redirects instead of JSON.
Follows the same pattern as API error handlers.
"""

from flask import Blueprint


def attach_web_err_handlers(bp: Blueprint) -> None:
    """Register common HTML/redirect error handlers on the given web blueprint."""
    
    from .http import add_web_http_err_handlers
    from .db import add_web_db_err_handlers
    from .unexpected import add_web_unexpected_err_handler

    # HTTPException → redirect or show error page
    add_web_http_err_handlers(bp)

    # Database errors → show error page
    add_web_db_err_handlers(bp)

    # Catch-all → show error page
    add_web_unexpected_err_handler(bp)
