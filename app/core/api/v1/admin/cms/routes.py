"""
Admin CMS routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response import (
    SuccessResp,
    CreatedResp,
    BadRequestResp,
    UnauthorizedResp,
    ForbiddenResp,
    NotFoundResp,
    ConflictResp,
    ServerErrorResp,
)
from app.schemas.admin import CmsPageCreateRequest, CmsPageUpdateRequest
from app.utils.decorators.auth import roles_required
from .controllers import AdminCmsController
from . import bp


@bp.get("/pages")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - CMS"],
    summary="List CMS Pages",
    description="List all CMS pages. Requires admin role.",
    responses={
        "200": SuccessResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
        "500": ServerErrorResp,
    },
)
def list_pages():
    """List all CMS pages."""
    return AdminCmsController.list_pages()


@bp.post("/pages")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=CmsPageCreateRequest,
    tags=["Admin - CMS"],
    summary="Create CMS Page",
    description="Create a new CMS page. Requires admin role.",
    responses={
        "201": CreatedResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
        "409": ConflictResp,
        "500": ServerErrorResp,
    },
)
def create_page():
    """Create a new CMS page."""
    return AdminCmsController.create_page()


@bp.patch("/pages/<page_id>")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=CmsPageUpdateRequest,
    tags=["Admin - CMS"],
    summary="Update CMS Page",
    description="Update a CMS page. Requires admin role.",
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
        "404": NotFoundResp,
        "409": ConflictResp,
        "500": ServerErrorResp,
    },
)
def update_page(page_id: str):
    """Update a CMS page."""
    return AdminCmsController.update_page(page_id)


@bp.delete("/pages/<page_id>")
@roles_required("Super Admin", "Admin")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - CMS"],
    summary="Delete CMS Page",
    description="Delete a CMS page. Requires Super Admin or Admin role.",
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
        "404": NotFoundResp,
        "500": ServerErrorResp,
    },
)
def delete_page(page_id: str):
    """Delete a CMS page."""
    return AdminCmsController.delete_page(page_id)

