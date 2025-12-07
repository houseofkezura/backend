"""
Public CMS routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint
from app.schemas.response import SuccessResponse, ErrorResponse
from .controllers import CmsController
from . import bp


@bp.get("/pages/<slug>")
@endpoint(
    tags=["CMS"],
    summary="Get CMS Page",
    description="Get a published CMS page by slug. No authentication required."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def get_page(slug: str):
    """Get CMS page by slug."""
    return CmsController.get_page(slug)

