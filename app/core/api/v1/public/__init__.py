from flask import Blueprint

from .auth import auth_routes
from .orders import orders_routes
from .payment import payment_routes
from .stats import stats_routes
from .profile import profile_routes
from .products import bp as products_bp
from .cart import bp as cart_bp
from .wishlist import bp as wishlist_bp
from .checkout import bp as checkout_bp
from .loyalty import bp as loyalty_bp
from .crm import bp as crm_bp
from .revamps import bp as revamps_bp
from .b2b import bp as b2b_bp
from .cms import bp as cms_bp
from .addresses import bp as addresses_bp
from .shipping import bp as shipping_bp
from .inventory import bp as inventory_bp

def create_api_v1_public_blueprint():
    bp: Blueprint = Blueprint("api_v1_public", __name__, url_prefix="/") 
    bp.register_blueprint(auth_routes.bp)
    bp.register_blueprint(orders_routes.bp)
    bp.register_blueprint(payment_routes.bp)
    bp.register_blueprint(stats_routes.bp)
    bp.register_blueprint(profile_routes.bp)
    bp.register_blueprint(products_bp)
    bp.register_blueprint(cart_bp)
    bp.register_blueprint(wishlist_bp)
    bp.register_blueprint(checkout_bp)
    bp.register_blueprint(loyalty_bp)
    bp.register_blueprint(crm_bp)
    bp.register_blueprint(revamps_bp)
    bp.register_blueprint(b2b_bp)
    bp.register_blueprint(cms_bp)
    bp.register_blueprint(addresses_bp)
    bp.register_blueprint(shipping_bp)
    bp.register_blueprint(inventory_bp)
    return bp