"""
Admin CMS routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
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
    description="List all CMS pages. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_500=ErrorResponse))
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
    description="Create a new CMS page. Requires admin role."
)
@spec.validate(resp=Response(HTTP_201=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_409=ErrorResponse, HTTP_500=ErrorResponse))
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
    description="Update a CMS page. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_409=ErrorResponse, HTTP_500=ErrorResponse))
def update_page(page_id: str):
    """Update a CMS page."""
    return AdminCmsController.update_page(page_id)


@bp.delete("/pages/<page_id>")
@roles_required("Super Admin", "Admin")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - CMS"],
    summary="Delete CMS Page",
    description="Delete a CMS page. Requires Super Admin or Admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def delete_page(page_id: str):
    """Delete a CMS page."""
    return AdminCmsController.delete_page(page_id)

