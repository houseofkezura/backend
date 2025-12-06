from __future__ import annotations

from flask_jwt_extended import jwt_required
from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
from app.schemas.profile import UpdateProfileRequest
from .controllers import ProfileController
from . import bp


@bp.get("")
@jwt_required()
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Profile"],
    summary="Get User Profile",
    description="Get the authenticated user's complete profile details including profile information, address, and wallet"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse))
def get_profile():
    """Get the current user's profile."""
    return ProfileController.get_profile()


@bp.patch("")
@jwt_required()
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=UpdateProfileRequest,
    tags=["Profile"],
    summary="Update User Profile",
    description="Update the authenticated user's profile details. All fields are optional - only provided fields will be updated."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_409=ErrorResponse))
def update_profile():
    """Update the current user's profile."""
    return ProfileController.update_profile()

