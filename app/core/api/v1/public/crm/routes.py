"""
Public CRM routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, QueryParameter
from app.schemas.response import (
    CreatedResp,
    BadRequestResp,
    UnauthorizedResp,
    NotFoundResp,
    ConflictResp,
    ServerErrorResp,
)
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
        "201": CreatedResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
        "404": NotFoundResp,
        "409": ConflictResp,
        "500": ServerErrorResp,
    },
)
def create_rating():
    """Create a CRM staff rating."""
    return CrmController.create_rating()




