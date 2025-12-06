from flask import Blueprint

from .auth import auth_routes
from .offers import offers_routes
from .orders import orders_routes
from .esim import esim_routes
from .payment import payment_routes
from .stats import stats_routes
from .profile import profile_routes

def create_api_v1_public_blueprint():
    bp: Blueprint = Blueprint("api_v1_public", __name__, url_prefix="/") 
    bp.register_blueprint(auth_routes.bp)
    bp.register_blueprint(offers_routes.bp)
    bp.register_blueprint(orders_routes.bp)
    bp.register_blueprint(esim_routes.bp)
    bp.register_blueprint(payment_routes.bp)
    bp.register_blueprint(stats_routes.bp)
    bp.register_blueprint(profile_routes.bp)
    return bp