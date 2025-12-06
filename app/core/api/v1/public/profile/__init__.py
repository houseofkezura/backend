from flask import Blueprint

bp: Blueprint = Blueprint("api_v1_profile", __name__, url_prefix="/profile")

from . import routes as profile_routes

