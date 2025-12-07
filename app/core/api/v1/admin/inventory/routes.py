"""
Admin inventory routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
from app.schemas.products import InventoryAdjustRequest
from app.utils.decorators.auth import roles_required
from .controllers import AdminInventoryController
from . import bp


@bp.post("/adjust")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=InventoryAdjustRequest,
    tags=["Admin - Inventory"],
    summary="Adjust Inventory",
    description="Adjust inventory quantity for a product variant. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def adjust_inventory():
    """Adjust inventory."""
    return AdminInventoryController.adjust_inventory()

