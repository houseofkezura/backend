"""
Admin inventory controller.
"""

from __future__ import annotations

from flask import Response, request
import uuid

from app.extensions import db
from app.models.product import ProductVariant, Inventory
from app.models.audit import AuditLog
from app.schemas.products import InventoryAdjustRequest
from app.utils.helpers.api_response import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class AdminInventoryController:
    """Controller for admin inventory endpoints."""

    @staticmethod
    def adjust_inventory() -> Response:
        """
        Adjust inventory for a product variant.
        
        Requires admin authentication.
        Creates audit log entry.
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            payload = InventoryAdjustRequest.model_validate(request.get_json())
            
            try:
                variant_uuid = uuid.UUID(payload.variant_id)
            except ValueError:
                return error_response("Invalid variant ID format", 400)
            
            variant = ProductVariant.query.get(variant_uuid)
            if not variant:
                return error_response("Variant not found", 404)
            
            # Get or create inventory
            inventory = variant.inventory
            if not inventory:
                inventory = Inventory()
                inventory.variant_id = variant_uuid
                inventory.quantity = 0
                inventory.low_stock_threshold = 5
                db.session.add(inventory)
                db.session.flush()
            
            old_quantity = inventory.quantity
            
            # Adjust quantity
            if payload.adjust_delta:
                inventory.quantity += payload.quantity
            else:
                inventory.quantity = payload.quantity
            
            if payload.low_stock_threshold is not None:
                inventory.low_stock_threshold = payload.low_stock_threshold
            
            db.session.commit()
            
            # Create audit log
            AuditLog.log_action(
                action="inventory_adjust",
                user_id=current_user.id,
                resource_type="inventory",
                resource_id=variant_uuid,
                meta={
                    "variant_sku": variant.sku,
                    "old_quantity": old_quantity,
                    "new_quantity": inventory.quantity,
                    "adjust_delta": payload.adjust_delta,
                }
            )
            
            log_event(f"Inventory adjusted: {variant.sku} from {old_quantity} to {inventory.quantity}")
            
            return success_response(
                "Inventory adjusted successfully",
                200,
                {"inventory": inventory.to_dict()}
            )
        except Exception as e:
            log_error("Failed to adjust inventory", error=e)
            db.session.rollback()
            return error_response("Failed to adjust inventory", 500)

