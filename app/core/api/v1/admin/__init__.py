from flask import Blueprint

from .auth import auth_routes

def create_api_v1_admin_blueprint():
    bp: Blueprint = Blueprint("api_v1_admin", __name__, url_prefix="/admin") 
    bp.register_blueprint(auth_routes.bp)
    return bp