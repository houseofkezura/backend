from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response import SuccessResp, BadRequestResp, UnauthorizedResp, ConflictResp
from app.schemas.profile import UpdateProfileRequest
from app.utils.decorators.auth import customer_required
from .controllers import ProfileController
from . import bp


@bp.get("")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Profile"],
    summary="Get User Profile",
    description="Get the authenticated user's complete profile details including profile information, address, and wallet",
    responses={
        "200": SuccessResp,
        "401": UnauthorizedResp,
    },
)
def get_profile():
    """Get the current user's profile."""
    return ProfileController.get_profile()


@bp.patch("")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=UpdateProfileRequest,
    tags=["Profile"],
    summary="Update User Profile",
    description="Update the authenticated user's profile details. All fields are optional - only provided fields will be updated.",
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
        "409": ConflictResp,
    },
)
def update_profile():
    """Update the current user's profile."""
    return ProfileController.update_profile()

