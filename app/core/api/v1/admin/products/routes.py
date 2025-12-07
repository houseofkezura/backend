"""
Admin product routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
from app.schemas.products import CreateProductRequest, UpdateProductRequest
from app.utils.decorators.auth import roles_required
from .controllers import AdminProductController
from . import bp


@bp.post("")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=CreateProductRequest,
    tags=["Admin - Products"],
    summary="Create Product",
    description="Create a new product with optional variants. Requires admin role."
)
@spec.validate(resp=Response(HTTP_201=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_409=ErrorResponse, HTTP_500=ErrorResponse))
def create_product():
    """Create a new product."""
    return AdminProductController.create_product()


@bp.patch("/<product_id>")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=UpdateProductRequest,
    tags=["Admin - Products"],
    summary="Update Product",
    description="Update a product. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_409=ErrorResponse, HTTP_500=ErrorResponse))
def update_product(product_id: str):
    """Update a product."""
    return AdminProductController.update_product(product_id)

