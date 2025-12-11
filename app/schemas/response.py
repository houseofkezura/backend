"""Common Pydantic schemas used in API responses."""

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
    message: str = "Forbidden"
    status_code: int = 403

class NotFoundResp(ErrorResp):
    """Not found response schema."""
    message: str = "Not found"
    status_code: int = 404

class ConflictResp(ErrorResp):
    """Conflict response schema."""
    message: str = "Conflict"
    status_code: int = 409

class TooManyRequestsResp(ErrorResp):
    """Too many requests response schema."""
    message: str = "Too many requests"
    status_code: int = 429

class ServerErrorResp(ErrorResp):
    """Internal server error response schema."""
    message: str = "Internal server error"
    status_code: int = 500

# Backwards-compatible aliases for legacy response names
SuccessResponse = SuccessResp
ErrorResponse = ErrorResp
CreatedResponse = CreatedResp
NoContentResponse = NoContentResp
BadRequestResponse = BadRequestResp
UnauthorizedResponse = UnauthorizedResp
ForbiddenResponse = ForbiddenResp
NotFoundResponse = NotFoundResp
ConflictResponse = ConflictResp
TooManyRequestsResponse = TooManyRequestsResp
ServerErrorResponse = ServerErrorResp