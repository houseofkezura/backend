"""
Admin user routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
from app.schemas.admin import AssignRoleRequest
from app.utils.decorators.auth import roles_required
from .controllers import AdminUserController
from . import bp


@bp.get("")
@roles_required("Super Admin", "Admin", "Operations", "CRM Manager")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Users"],
    summary="List Users",
    description="List all users with filtering and pagination. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_500=ErrorResponse))
def list_users():
    """List all users."""
    return AdminUserController.list_users()


@bp.get("/<user_id>")
@roles_required("Super Admin", "Admin", "Operations", "CRM Manager")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Users"],
    summary="Get User",
    description="Get a single user by ID. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def get_user(user_id: str):
    """Get a user by ID."""
    return AdminUserController.get_user(user_id)


@bp.post("/<user_id>/roles")
@roles_required("Super Admin", "Admin")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=AssignRoleRequest,
    tags=["Admin - Users"],
    summary="Assign Role",
    description="Assign a role to a user. Requires Super Admin or Admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_409=ErrorResponse, HTTP_500=ErrorResponse))
def assign_role(user_id: str):
    """Assign a role to a user."""
    return AdminUserController.assign_role(user_id)


@bp.delete("/<user_id>/roles")
@roles_required("Super Admin", "Admin")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=AssignRoleRequest,
    tags=["Admin - Users"],
    summary="Revoke Role",
    description="Revoke a role from a user. Requires Super Admin or Admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def revoke_role(user_id: str):
    """Revoke a role from a user."""
    return AdminUserController.revoke_role(user_id)


@bp.post("/<user_id>/deactivate")
@roles_required("Super Admin", "Admin")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Users"],
    summary="Deactivate User",
    description="Deactivate a user account. Requires Super Admin or Admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def deactivate_user(user_id: str):
    """Deactivate a user."""
    return AdminUserController.deactivate_user(user_id)

