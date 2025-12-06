from flask import Blueprint

bp: Blueprint = Blueprint("api_v1_stats", __name__, url_prefix="/stats")

from . import routes as stats_routes

