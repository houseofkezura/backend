

from .logging import log_event
# from .utils.helpers.user import get_app_user_info
from .extensions import db

def app_context_Processor():
    user_id = None
    
    # current_user_info = get_app_user_info(user_id)
    
    
    return {
        'CURRENT_USER': {},
        'SITE_INFO': {
            "site_title": "House Of Kezura",
            "site_tagline": "Luxury African Beauty E-Commerce Platform",
            "currency": "NGN",
        },
    }