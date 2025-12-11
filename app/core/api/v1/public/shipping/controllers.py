"""
Shipping controller for public shipping endpoints.
"""

from __future__ import annotations

from flask import Response, request

from quas_utils.api import success_response, error_response
from app.utils.checkout.service import calculate_shipping_cost
from app.logging import log_error


class ShippingController:
    """Controller for public shipping endpoints."""

    @staticmethod
    def get_shipping_zones() -> Response:
        """
        Get shipping zones and methods for a country.
        
        Public endpoint - no authentication required.
        """
        try:
            country = request.args.get("country", "NG").upper()
            
            # Zone 1: Nigeria
            if country == "NG":
                zones = {
                    "zone": "Zone 1 - Nigeria",
                    "country": country,
                    "methods": [
                        {
                            "name": "standard",
                            "label": "Standard Shipping",
                            "cost_ngn": 3000.0,
                            "estimated_days": "3-5 business days",
                        },
                        {
                            "name": "express",
                            "label": "Express Shipping",
                            "cost_ngn": 5000.0,
                            "estimated_days": "1-2 business days",
                        },
                    ],
                }
            # Zone 2: Rest of Africa
            elif country in ["GH", "KE", "ZA", "EG", "ET", "TZ", "UG", "RW", "ZM", "ZW"]:
                zones = {
                    "zone": "Zone 2 - Rest of Africa",
                    "country": country,
                    "methods": [
                        {
                            "name": "standard",
                            "label": "Standard Shipping",
                            "cost_ngn": 10000.0,
                            "estimated_days": "7-10 business days",
                        },
                        {
                            "name": "express",
                            "label": "Express Shipping",
                            "cost_ngn": 15000.0,
                            "estimated_days": "5-7 business days",
                        },
                    ],
                }
            # Zone 3: International
            else:
                zones = {
                    "zone": "Zone 3 - International",
                    "country": country,
                    "methods": [
                        {
                            "name": "standard",
                            "label": "Standard Shipping",
                            "cost_ngn": 20000.0,
                            "estimated_days": "10-14 business days",
                        },
                        {
                            "name": "express",
                            "label": "Express Shipping",
                            "cost_ngn": 25000.0,
                            "estimated_days": "5-7 business days",
                        },
                    ],
                }
            
            return success_response(
                "Shipping zones retrieved successfully",
                200,
                zones
            )
        except Exception as e:
            log_error("Failed to get shipping zones", error=e)
            return error_response("Failed to retrieve shipping zones", 500)




