from flask import Blueprint

bp = Blueprint("admin_orders", __name__, url_prefix="/orders")

from . import routes

