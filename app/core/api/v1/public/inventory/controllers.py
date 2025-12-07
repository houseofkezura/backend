"""
Inventory controller for public inventory endpoints.
"""

from __future__ import annotations

from flask import Response

from app.extensions import db
from app.models.product import ProductVariant, Inventory
from app.utils.helpers.api_response import success_response, error_response
from app.logging import log_error


class InventoryController:
    """Controller for public inventory endpoints."""

    @staticmethod
    def get_inventory_by_sku(sku: str) -> Response:
        """
        Get inventory information for a product variant by SKU.
        
        Public endpoint - no authentication required.
        
        Args:
            sku: Product variant SKU
        """
        try:
            variant = ProductVariant.query.filter_by(sku=sku).first()
            
            if not variant:
                return error_response("Product variant not found", 404)
            
            inventory_data = {
                "sku": variant.sku,
                "variant_id": str(variant.id),
                "product_id": str(variant.product_id),
                "is_in_stock": variant.is_in_stock,
                "stock_quantity": variant.stock_quantity,
            }
            
            if variant.inventory:
                inventory_data["low_stock_threshold"] = variant.inventory.low_stock_threshold
                inventory_data["is_low_stock"] = variant.inventory.is_low_stock
            
            return success_response(
                "Inventory information retrieved successfully",
                200,
                {"inventory": inventory_data}
            )
        except Exception as e:
            log_error(f"Failed to get inventory for SKU {sku}", error=e)
            return error_response("Failed to retrieve inventory information", 500)

