"""
Lightweight console logging helpers used across the codebase.

These helpers are thin wrappers over the central logging configured in
`app.logging`. They are kept for backward compatibility with existing imports
throughout the project.
"""

from __future__ import annotations

import logging
from typing import Any

from flask import has_app_context, current_app


def _get_logger() -> logging.Logger:
    """Return the appropriate logger depending on app context."""
    return current_app.logger if has_app_context() else logging.getLogger(__name__)


def console_log(key: str, value: Any) -> None:
    """
    Log a simple key/value pair at INFO level.

    Args:
        key: A short key or label for the log entry
        value: The value to log; will be converted to string
    """
    logger = _get_logger()
    logger.info(str(value), extra={"event_type": key})


def log_exception(context: str, error: BaseException) -> None:
    """
    Log an exception with context. This does not re-raise the error.

    Args:
        context: Description of the operation being performed
        error: The exception instance
    """
    logger = _get_logger()
    logger.exception(str(context), extra={"error_type": error.__class__.__name__})

