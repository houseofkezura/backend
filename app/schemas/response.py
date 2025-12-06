"""Common Pydantic schemas used in API responses."""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel
from typing_extensions import Literal


class ApiResponse(BaseModel):
    """Canonical API response envelope."""

    status: Literal['success', 'failed']
    status_code: int
    message: str
    data: Optional[Any] = None

class ErrorResponse(ApiResponse):
    """Error response schema."""
    
    status: Literal['failed']
    errors: Optional[List[str]] = None

class SuccessResponse(ApiResponse):
    """Success response schema."""
    
    status: Literal['success']
    data: Optional[Any] = None