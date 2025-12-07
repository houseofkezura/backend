"""
Address management controller.
"""

from __future__ import annotations

from flask import Response, request
import uuid

from app.extensions import db
from app.models.user import Address
from app.schemas.addresses import CreateAddressRequest, UpdateAddressRequest
from app.utils.helpers.api_response import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error


class AddressController:
    """Controller for address management endpoints."""

    @staticmethod
    def list_addresses() -> Response:
        """
        Get all addresses for the authenticated user.
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            addresses = Address.query.filter_by(user_id=current_user.id).order_by(
                Address.is_default.desc(),
                Address.created_at.desc()
            ).all()
            
            return success_response(
                "Addresses retrieved successfully",
                200,
                {"addresses": [addr.to_dict() for addr in addresses]}
            )
        except Exception as e:
            log_error("Failed to get addresses", error=e)
            return error_response("Failed to retrieve addresses", 500)

    @staticmethod
    def create_address() -> Response:
        """
        Create a new address for the authenticated user.
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            payload = CreateAddressRequest.model_validate(request.get_json())
            
            # If setting as default, unset other defaults
            if payload.is_default:
                Address.query.filter_by(user_id=current_user.id, is_default=True).update({"is_default": False})
            
            address = Address()
            address.user_id = current_user.id
            address.label = payload.label
            address.line1 = payload.line1
            address.line2 = payload.line2
            address.city = payload.city
            address.state = payload.state
            address.postal_code = payload.postal_code
            address.country = payload.country
            address.is_default = payload.is_default
            
            db.session.add(address)
            db.session.commit()
            
            return success_response(
                "Address created successfully",
                201,
                {"address": address.to_dict()}
            )
        except Exception as e:
            log_error("Failed to create address", error=e)
            db.session.rollback()
            return error_response("Failed to create address", 500)

    @staticmethod
    def update_address(address_id: str) -> Response:
        """
        Update an address.
        
        Args:
            address_id: Address ID
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                addr_uuid = uuid.UUID(address_id)
            except ValueError:
                return error_response("Invalid address ID format", 400)
            
            address = Address.query.filter_by(id=addr_uuid, user_id=current_user.id).first()
            if not address:
                return error_response("Address not found", 404)
            
            payload = UpdateAddressRequest.model_validate(request.get_json())
            
            # If setting as default, unset other defaults
            if payload.is_default is True:
                Address.query.filter_by(user_id=current_user.id, is_default=True).update({"is_default": False})
            
            # Update fields
            if payload.label is not None:
                address.label = payload.label
            if payload.line1 is not None:
                address.line1 = payload.line1
            if payload.line2 is not None:
                address.line2 = payload.line2
            if payload.city is not None:
                address.city = payload.city
            if payload.state is not None:
                address.state = payload.state
            if payload.postal_code is not None:
                address.postal_code = payload.postal_code
            if payload.country is not None:
                address.country = payload.country
            if payload.is_default is not None:
                address.is_default = payload.is_default
            
            db.session.commit()
            
            return success_response(
                "Address updated successfully",
                200,
                {"address": address.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to update address {address_id}", error=e)
            db.session.rollback()
            return error_response("Failed to update address", 500)

    @staticmethod
    def delete_address(address_id: str) -> Response:
        """
        Delete an address.
        
        Args:
            address_id: Address ID
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                addr_uuid = uuid.UUID(address_id)
            except ValueError:
                return error_response("Invalid address ID format", 400)
            
            address = Address.query.filter_by(id=addr_uuid, user_id=current_user.id).first()
            if not address:
                return error_response("Address not found", 404)
            
            db.session.delete(address)
            db.session.commit()
            
            return success_response("Address deleted successfully", 200)
        except Exception as e:
            log_error(f"Failed to delete address {address_id}", error=e)
            db.session.rollback()
            return error_response("Failed to delete address", 500)

