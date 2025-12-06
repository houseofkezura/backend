import json
import logging
from flask import current_app, has_app_context, Flask

def configure_logging(app: Flask) -> None:
    """
    Configure application logging.

    In production, use structured JSON logs. In other environments, use a
    simple human-readable format.

    Args:
        app: The Flask application instance
    """
    if app.logger.hasHandlers():
        app.logger.handlers.clear()

    handler = logging.StreamHandler()

    if app.config.get("ENV") == "production":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(DevFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))

    app.logger.addHandler(handler)
    app.logger.setLevel(app.config.get("LOG_LEVEL", "INFO"))


class JsonFormatter(logging.Formatter):
    """Structured JSON log formatter for production"""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Attach any extra context if provided
        for key in ("event_type", "error_type", "message_text", "error_text", "data"):
            if hasattr(record, key):
                value = getattr(record, key)
                # Ensure JSON serializable for complex objects
                try:
                    json.dumps(value)
                    log_entry[key] = value
                except Exception:
                    log_entry[key] = repr(value)

        return json.dumps(log_entry)


def log_event(message: str | None = None, data: object | None = None, event_type: str | None = None, **kwargs) -> None:
    """
    Log a structured informational event.

    Usage:
    - log_event("did something")
    - log_event("email_username", email)
    - log_event(data=<obj>)  # if message omitted, log the data itself

    The human-readable message is kept in the main message field; structured
    fields are added under extras so they are separately visible in JSON and
    in dev output.
    """
    logger = current_app.logger if has_app_context() else logging.getLogger(__name__)
    if event_type is None:
        event_type = "event"

    # Determine primary text and extras
    primary_text = message if message is not None else (repr(data) if data is not None else "")
    extra = {"event_type": event_type, **kwargs}
    if message is not None:
        extra["message_text"] = message
    if data is not None:
        extra["data"] = data

    logger.info(primary_text, extra=extra)


def log_error(message: str | None = None, error: Exception | str | None = None, *, error_type: str | None = None, exc_info=None, **kwargs) -> None:
    """
    Log an error with flexible inputs and clear separation of message and error.

    Usage:
    - log_error("a message/info", err) -> logs both message and error
    - log_error("only a message") -> logs message only
    - log_error(error=err) or log_error(None, err) -> logs error only

    If an Exception is provided and exc_info is not set, a traceback is attached.
    """
    logger = current_app.logger if has_app_context() else logging.getLogger(__name__)

    # Determine error type/category
    derived_error_type = error.__class__.__name__ if isinstance(error, BaseException) else None
    if error_type is None:
        error_type = derived_error_type or "error"

    # Derive text fields
    message_text = message if message is not None else None
    error_text = None
    if error is not None:
        error_text = repr(error) if not isinstance(error, str) else error

    # Determine the primary log message
    primary_text = message_text if message_text is not None else (error_text or "")

    # Normalize exc_info: accept Exception instance or tuple/bool
    normalized_exc_info = exc_info
    if normalized_exc_info is None and isinstance(error, BaseException):
        normalized_exc_info = (type(error), error, error.__traceback__)
    elif isinstance(normalized_exc_info, BaseException):
        normalized_exc_info = (type(normalized_exc_info), normalized_exc_info, normalized_exc_info.__traceback__)

    extra = {"error_type": error_type, **kwargs}
    if message_text is not None:
        extra["message_text"] = message_text
    if error_text is not None:
        extra["error_text"] = error_text

    logger.error(primary_text, extra=extra, exc_info=normalized_exc_info)


class DevFormatter(logging.Formatter):
    """Human-readable log formatter that surfaces structured extras.

    Appends message_text, error_text, data, and type fields when present.
    """

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        base = super().format(record)
        parts: list[str] = []
        if hasattr(record, "event_type"):
            parts.append(f"event_type={getattr(record, 'event_type')}")
        if hasattr(record, "error_type"):
            parts.append(f"error_type={getattr(record, 'error_type')}")
        if hasattr(record, "message_text"):
            parts.append(f"msg={getattr(record, 'message_text')}")
        if hasattr(record, "error_text"):
            parts.append(f"error={getattr(record, 'error_text')}")
        if hasattr(record, "data"):
            parts.append(f"data={getattr(record, 'data')}")
        return base + (" | " + " ".join(parts) if parts else "")