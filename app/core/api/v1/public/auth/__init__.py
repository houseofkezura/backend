from flask import Blueprint

bp: Blueprint = Blueprint("api_v1_auth", __name__, url_prefix="/auth")

from . import routes as auth_routes