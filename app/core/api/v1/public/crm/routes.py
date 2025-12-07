"""
Public CRM routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, QueryParameter
from app.schemas.response import SuccessResponse, ErrorResponse
from app.schemas.crm import CreateRatingRequest
from .controllers import CrmController
from . import bp


@bp.post("/ratings")
@endpoint(
    request_body=CreateRatingRequest,
    tags=["CRM"],
    summary="Rate CRM Staff",
    description="Submit a rating for the CRM staff member who packed your order. Requires order to be delivered. For guest orders, include email query param.",
    query_params=[
        QueryParameter("email", "string", required=False, description="Email for guest orders"),
    ]
)
@spec.validate(resp=Response(HTTP_201=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_404=ErrorResponse, HTTP_409=ErrorResponse, HTTP_500=ErrorResponse))
def create_rating():
    """Create a CRM staff rating."""
    return CrmController.create_rating()

