"""
Public address management routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response_data import (
    AddressListData,
    AddressData,
    ValidationErrorData,
)
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
    description="Get all addresses for the authenticated user",
    responses={
        "200": AddressListData,
        "401": None,
        "500": None,
    },
)
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
    description="Create a new address for the authenticated user",
    responses={
        "201": AddressData,
        "400": ValidationErrorData,
        "401": None,
        "500": None,
    },
)
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
    description="Update an address",
    responses={
        "200": AddressData,
        "400": ValidationErrorData,
        "401": None,
        "404": None,
        "500": None,
    },
)
def update_address(address_id: str):
    """Update an address."""
    return AddressController.update_address(address_id)


@bp.delete("/<address_id>")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Addresses"],
    summary="Delete Address",
    description="Delete an address",
    responses={
        "200": None,
        "401": None,
        "404": None,
        "500": None,
    },
)
def delete_address(address_id: str):
    """Delete an address."""
    return AddressController.delete_address(address_id)




