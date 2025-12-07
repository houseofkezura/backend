"""
Public B2B inquiry routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint
from app.schemas.response import SuccessResponse, ErrorResponse
from app.schemas.b2b import CreateB2BInquiryRequest
from .controllers import B2BController
from . import bp


@bp.post("/inquiries")
@endpoint(
    request_body=CreateB2BInquiryRequest,
    tags=["B2B"],
    summary="Submit B2B Inquiry",
    description="Submit a wholesale/B2B inquiry. No authentication required."
)
@spec.validate(resp=Response(HTTP_201=SuccessResponse, HTTP_400=ErrorResponse, HTTP_500=ErrorResponse))
def create_inquiry():
    """Create a B2B inquiry."""
    return B2BController.create_inquiry()

