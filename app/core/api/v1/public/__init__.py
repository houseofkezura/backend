from flask import Blueprint

from .auth import auth_routes
from .orders import orders_routes
from .payment import payment_routes
from .stats import stats_routes
from .profile import profile_routes
from .products import bp as products_bp

def create_api_v1_public_blueprint():
    bp: Blueprint = Blueprint("api_v1_public", __name__, url_prefix="/") 
    bp.register_blueprint(auth_routes.bp)
    bp.register_blueprint(orders_routes.bp)

    bp.register_blueprint(payment_routes.bp)
    bp.register_blueprint(stats_routes.bp)
    bp.register_blueprint(profile_routes.bp)
    bp.register_blueprint(products_bp)
    return bp