"""
Reusable error handler attachment for API blueprints.

Attaches common handlers (HTTP, DB, JWT, generic) to a given blueprint so
endpoints can avoid repetitive try/except blocks and always return JSON.
"""

from flask import Blueprint



def attach_api_err_handlers(bp: Blueprint) -> None:
    """Register common JSON error handlers on the given blueprint."""
    
    from .http import add_http_err_handlers
    from .jwt import add_jwt_err_handler
    from .email import add_email_err_handler
    from .pydantic import add_pydantic_err_handlers
    from .db import add_db_err_handlers
    from .unexpected import add_unexpected_err_handler

    # HTTPException → use provided code/description
    add_http_err_handlers(bp)

    # JWT / auth errors → 401/403
    add_jwt_err_handler(bp)

    # Email validation errors → 400 with message
    add_email_err_handler(bp)

    # Pydantic validation errors → 400 with structured details
    add_pydantic_err_handlers(bp)

    # Database errors → rollback and return appropriate code
    add_db_err_handlers(bp)

    # Catch-all → 500
    add_unexpected_err_handler(bp)


