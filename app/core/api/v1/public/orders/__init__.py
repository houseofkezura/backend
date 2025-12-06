from flask import Blueprint

bp: Blueprint = Blueprint("api_v1_orders", __name__, url_prefix="/orders")

from . import routes as orders_routes


