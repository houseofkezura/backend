"""Common Pydantic schemas used in API responses.

DEPRECATED: These schemas are deprecated in favor of data schemas in response_data.py.
The quas-docs package now automatically wraps data schemas in base response envelopes.
These schemas are kept for backward compatibility but should not be used in new code.
"""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel
from typing_extensions import Literal


class ApiResp(BaseModel):
    """Canonical API response envelope."""

    status: Literal['success', 'failed']
    status_code: int
    message: str
    data: Optional[dict] = {}

class ErrorResp(ApiResp):
    """Error response schema."""
    
    status: Literal['failed']
    errors: Optional[List[str]] = None
    status_code: int = 400

class SuccessResp(ApiResp):
    """Success response schema."""
    
    status: Literal['success']
    status_code: int = 200

class CreatedResp(SuccessResp):
    """Created response schema."""
    status_code: int = 201

class NoContentResp(SuccessResp):
    """No content response schema."""
    status_code: int = 204

class BadRequestResp(ErrorResp):
    """Bad request response schema."""
    status_code: int = 400

class UnauthorizedResp(ErrorResp):
    """Unauthorized response schema."""
    status_code: int = 401

class ForbiddenResp(ErrorResp):
    """Forbidden response schema."""
    status_code: int = 403

class NotFoundResp(ErrorResp):
    """Not found response schema."""
    status_code: int = 404