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

    @staticmethod
    def list_inventory() -> Response:
        """
        List all inventory with optional filtering.
        
        Requires admin authentication.
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            # Get query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            low_stock_only = request.args.get('low_stock_only', False, type=bool)
            sku = request.args.get('sku', type=str)
            
            # Build query
            query = db.session.query(Inventory).join(ProductVariant)
            
            if low_stock_only:
                query = query.filter(Inventory.quantity <= Inventory.low_stock_threshold)
            
            if sku:
                query = query.filter(ProductVariant.sku.ilike(f'%{sku}%'))
            
            # Paginate
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            inventory_list = []
            for inv in pagination.items:
                inv_dict = inv.to_dict()
                if inv.variant:
                    inv_dict['variant'] = inv.variant.to_dict()
                    inv_dict['product'] = inv.variant.product.to_dict() if inv.variant.product else None
                inventory_list.append(inv_dict)
            
            return success_response(
                "Inventory retrieved successfully",
                200,
                {
                    "inventory": inventory_list,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages
                    }
                }
            )
        except Exception as e:
            log_error("Failed to list inventory", error=e)
            return error_response("Failed to retrieve inventory", 500)

    @staticmethod
    def get_inventory_by_sku(sku: str) -> Response:
        """
        Get inventory by SKU.
        
        Args:
            sku: Product variant SKU
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            variant = ProductVariant.query.filter_by(sku=sku).first()
            if not variant:
                return error_response("Variant not found", 404)
            
            inventory = variant.inventory
            if not inventory:
                return error_response("Inventory not found for this variant", 404)
            
            inv_dict = inventory.to_dict()
            inv_dict['variant'] = variant.to_dict()
            inv_dict['product'] = variant.product.to_dict() if variant.product else None
            
            return success_response(
                "Inventory retrieved successfully",
                200,
                {"inventory": inv_dict}
            )
        except Exception as e:
            log_error(f"Failed to get inventory for SKU {sku}", error=e)
            return error_response("Failed to retrieve inventory", 500)

