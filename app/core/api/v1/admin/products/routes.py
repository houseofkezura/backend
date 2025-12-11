"""
Admin product routes.
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
from app.schemas.products import CreateProductRequest, UpdateProductRequest, CreateProductVariantRequest, UpdateProductVariantRequest
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
    description="Create a new product with optional variants. Requires admin role.",
    responses={
        "201": CreatedResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
        "409": ConflictResp,
        "500": ServerErrorResp,
    },
)
def create_product():
    """Create a new product."""
    return AdminProductController.create_product()


@bp.get("")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Products"],
    summary="List Products",
    description="List all products with filtering and pagination. Requires admin role.",
    responses={
        "200": SuccessResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
        "500": ServerErrorResp,
    },
)
def list_products():
    """List all products."""
    return AdminProductController.list_products()


@bp.get("/<product_id>")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Products"],
    summary="Get Product",
    description="Get a single product by ID. Requires admin role.",
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
        "404": NotFoundResp,
        "500": ServerErrorResp,
    },
)
def get_product(product_id: str):
    """Get a product by ID."""
    return AdminProductController.get_product(product_id)


@bp.patch("/<product_id>")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=UpdateProductRequest,
    tags=["Admin - Products"],
    summary="Update Product",
    description="Update a product. Requires admin role.",
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
def update_product(product_id: str):
    """Update a product."""
    return AdminProductController.update_product(product_id)


@bp.delete("/<product_id>")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Products"],
    summary="Delete Product",
    description="Delete a product. Requires admin role.",
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
        "404": NotFoundResp,
        "500": ServerErrorResp,
    },
)
def delete_product(product_id: str):
    """Delete a product."""
    return AdminProductController.delete_product(product_id)


@bp.post("/<product_id>/variants")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=CreateProductVariantRequest,
    tags=["Admin - Products"],
    summary="Create Variant",
    description="Create a variant for a product. Requires admin role.",
    responses={
        "201": CreatedResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
        "404": NotFoundResp,
        "409": ConflictResp,
        "500": ServerErrorResp,
    },
)
def create_variant(product_id: str):
    """Create a variant for a product."""
    return AdminProductController.create_variant(product_id)


@bp.patch("/<product_id>/variants/<variant_id>")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=UpdateProductVariantRequest,
    tags=["Admin - Products"],
    summary="Update Variant",
    description="Update a product variant. Requires admin role.",
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
def update_variant(product_id: str, variant_id: str):
    """Update a variant."""
    return AdminProductController.update_variant(product_id, variant_id)


@bp.delete("/<product_id>/variants/<variant_id>")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Products"],
    summary="Delete Variant",
    description="Delete a product variant. Requires admin role.",
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
        "404": NotFoundResp,
        "500": ServerErrorResp,
    },
)
def delete_variant(product_id: str, variant_id: str):
    """Delete a variant."""
    return AdminProductController.delete_variant(product_id, variant_id)

