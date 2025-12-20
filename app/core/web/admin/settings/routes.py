from __future__ import annotations

from flask import render_template, request

from . import bp
from app.extensions import db
from app.models.settings import GeneralSetting, PaymentMethodSettings
from app.models.user import AppUser
from app.utils.app_settings.utils import get_all_general_settings, get_payment_method_settings
from .constants import PAYMENT_METHOD_OVERVIEW

@bp.route("/general", methods=['GET', 'POST'], strict_slashes=False)
def general_settings():
    page_name = "general settings"
    
    # Fetch all settings in a single query
    settings = get_all_general_settings()
    
    form = None
    
    if request.method == 'POST' and form.validate_on_submit():
        pass
    
    return render_template('admin/pages/settings/general_settings.html', page_name=page_name, form=form)

@bp.route("/payments", methods=['GET', 'POST'], strict_slashes=False)
def payment_settings():
    """
    Displays an overview of available payment methods.
    """
    page_name = "payment settings"
    
    # Add the current enabled status for each method
    payment_methods = []
    for overview in PAYMENT_METHOD_OVERVIEW:
        current_settings = get_payment_method_settings(overview["key"])
        
        payment_methods.append({
            **overview,
            "enabled": current_settings.get("enabled", "false").lower() == "true",
            "setup_url": overview["setup_url"](),  # Call lambda to generate URL
        })
    
    return render_template('admin/pages/settings/payment_settings.html', page_name=page_name, payment_methods=payment_methods)