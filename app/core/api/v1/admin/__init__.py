from flask import Blueprint

from .auth import auth_routes
from .products import bp as products_bp
from .inventory import bp as inventory_bp

def create_api_v1_admin_blueprint():
    bp: Blueprint = Blueprint("api_v1_admin", __name__, url_prefix="/admin") 
    bp.register_blueprint(auth_routes.bp)
    bp.register_blueprint(products_bp)
    bp.register_blueprint(inventory_bp)
    return bp