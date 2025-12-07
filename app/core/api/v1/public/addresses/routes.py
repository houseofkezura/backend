"""
Public address management routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
from app.schemas.addresses import CreateAddressRequest, UpdateAddressRequest
from app.utils.decorators.auth import customer_required
from .controllers import AddressController
from . import bp


@bp.get("")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Addresses"],
    summary="List Addresses",
    description="Get all addresses for the authenticated user"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_500=ErrorResponse))
def list_addresses():
    """List all addresses."""
    return AddressController.list_addresses()


@bp.post("")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=CreateAddressRequest,
    tags=["Addresses"],
    summary="Create Address",
    description="Create a new address for the authenticated user"
)
@spec.validate(resp=Response(HTTP_201=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_500=ErrorResponse))
def create_address():
    """Create a new address."""
    return AddressController.create_address()


@bp.put("/<address_id>")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=UpdateAddressRequest,
    tags=["Addresses"],
    summary="Update Address",
    description="Update an address"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def update_address(address_id: str):
    """Update an address."""
    return AddressController.update_address(address_id)


@bp.delete("/<address_id>")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Addresses"],
    summary="Delete Address",
    description="Delete an address"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def delete_address(address_id: str):
    """Delete an address."""
    return AddressController.delete_address(address_id)

