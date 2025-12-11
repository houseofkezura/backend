from __future__ import annotations

from typing import Any

from flask import Blueprint, request

from app.logging import log_error
from quas_utils.api import error_response


try:
    from pydantic import ValidationError as PydanticValidationError  # type: ignore
except Exception:  # pragma: no cover
    PydanticValidationError = type("PydanticValidationError", (), {})  # type: ignore

try:
    from pydantic_core import ValidationError as CoreValidationError  # type: ignore
except Exception:  # pragma: no cover
    CoreValidationError = type("CoreValidationError", (), {})  # type: ignore

# Pydantic validation errors → 400 with structured details
def _serialize_pydantic_errors(err: Any) -> list[dict[str, Any]]:
        try:
            return [
                {
                    "loc": list(getattr(e, "loc", ())),
                    "msg": getattr(e, "msg", str(e)),
                    "type": getattr(e, "type", "value_error"),
                }
                for e in err.errors()  # type: ignore[attr-defined]
            ]
        except Exception:
            return [{"msg": str(err)}]

def _handle_pydantic_validation(err: PydanticValidationError):  # type: ignore[name-defined]
    log_error("Validation error", err, path=request.path)
    return error_response("validation error", 400, {"errors": _serialize_pydantic_errors(err)})

def _handle_core_validation(err: CoreValidationError):  # type: ignore[name-defined]
    log_error("Validation error", err, path=request.path)
    return error_response("validation error", 400, {"errors": _serialize_pydantic_errors(err)})

def add_pydantic_err_handlers(bp: Blueprint):
    bp.register_error_handler(PydanticValidationError, _handle_pydantic_validation)  # type: ignore[arg-type]
    bp.register_error_handler(CoreValidationError, _handle_core_validation)  # type: ignore[arg-type]