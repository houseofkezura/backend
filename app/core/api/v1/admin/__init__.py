from flask import Blueprint

from .auth import auth_routes
from .products import bp as products_bp
from .inventory import bp as inventory_bp
from .orders import bp as orders_bp
from .users import bp as users_bp
from .loyalty import bp as loyalty_bp
from .staff import bp as staff_bp
from .cms import bp as cms_bp
from .b2b import bp as b2b_bp
from .crm import bp as crm_bp
from .revamps import bp as revamps_bp

def create_api_v1_admin_blueprint():
    bp: Blueprint = Blueprint("api_v1_admin", __name__, url_prefix="/admin") 
    bp.register_blueprint(auth_routes.bp)
    bp.register_blueprint(products_bp)
    bp.register_blueprint(inventory_bp)
    bp.register_blueprint(orders_bp)
    bp.register_blueprint(users_bp)
    bp.register_blueprint(loyalty_bp)
    bp.register_blueprint(staff_bp)
    bp.register_blueprint(cms_bp)
    bp.register_blueprint(b2b_bp)
    bp.register_blueprint(crm_bp)
    bp.register_blueprint(revamps_bp)
    return bp