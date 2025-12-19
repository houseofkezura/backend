

from flask import g

from .logging import log_event
# from .utils.helpers.user import get_app_user_info
from .extensions import db

def app_context_Processor():
    user = getattr(g, "current_user", None)
    current_user_payload = {}

    if user:
        current_user_payload = {
            "id": str(getattr(user, "id", "")) if getattr(user, "id", None) else None,
            "firstname": getattr(getattr(user, "profile", None), "firstname", None),
            "lastname": getattr(getattr(user, "profile", None), "lastname", None),
            "email": getattr(user, "email", None),
            "roles": [getattr(user_role.role.name, "value", None) for user_role in getattr(user, "roles", [])],
        }

    return {
        'CURRENT_USER': current_user_payload,
        'SITE_INFO': {
            "site_title": "House Of Kezura",
            "site_tagline": "Luxury African Beauty E-Commerce Platform",
            "currency": "NGN",
        },
    }