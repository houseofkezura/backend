"""
B2B inquiry controller for public endpoints.
"""

from __future__ import annotations

from flask import Response, request
import json

from app.extensions import db
from app.models.cms import B2BInquiry
from app.schemas.b2b import CreateB2BInquiryRequest
from app.utils.helpers.api_response import success_response, error_response
from app.logging import log_error, log_event


class B2BController:
    """Controller for public B2B inquiry endpoints."""

    @staticmethod
    def create_inquiry() -> Response:
        """
        Create a B2B wholesale inquiry.
        
        Public endpoint - no authentication required.
        """
        try:
            payload = CreateB2BInquiryRequest.model_validate(request.get_json())
            
            # Create inquiry
            inquiry = B2BInquiry()
            inquiry.business_name = payload.business_name
            inquiry.business_type = payload.business_type
            inquiry.contact_name = payload.contact_name
            inquiry.email = payload.email
            inquiry.phone = payload.phone
            inquiry.country = payload.country
            inquiry.expected_volume = payload.expected_volume
            inquiry.product_categories = json.dumps(payload.product_categories) if payload.product_categories else None
            inquiry.note = payload.note
            inquiry.status = "new"
            
            db.session.add(inquiry)
            db.session.commit()
            
            log_event(f"B2B inquiry created: {inquiry.id} from {payload.email}")
            
            # TODO: Send notification email to sales team
            
            return success_response(
                "Inquiry submitted successfully. Our B2B team will be in touch within 48 hours.",
                201,
                {"inquiry_id": str(inquiry.id)}
            )
        except Exception as e:
            log_error("Failed to create B2B inquiry", error=e)
            db.session.rollback()
            return error_response("Failed to submit inquiry", 500)

