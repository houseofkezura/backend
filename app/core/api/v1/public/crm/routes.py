"""
Public CRM routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, QueryParameter
from app.schemas.response_data import RatingData, ValidationErrorData
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
    ],
    responses={
        "201": RatingData,
        "400": ValidationErrorData,
        "401": None,
        "404": None,
        "409": None,
        "500": None,
    },
)
def create_rating():
    """Create a CRM staff rating."""
    return CrmController.create_rating()




