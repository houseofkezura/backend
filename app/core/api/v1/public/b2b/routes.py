"""
Public B2B inquiry routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint
from app.schemas.response_data import B2BInquiryData, ValidationErrorData
from app.schemas.b2b import CreateB2BInquiryRequest
from .controllers import B2BController
from . import bp


@bp.post("/inquiries")
@endpoint(
    request_body=CreateB2BInquiryRequest,
    tags=["B2B"],
    summary="Submit B2B Inquiry",
    description="Submit a wholesale/B2B inquiry. No authentication required.",
    responses={
        "201": B2BInquiryData,
        "400": ValidationErrorData,
        "500": None,
    },
)
def create_inquiry():
    """Create a B2B inquiry."""
    return B2BController.create_inquiry()




