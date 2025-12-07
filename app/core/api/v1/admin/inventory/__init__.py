from flask import Blueprint

bp = Blueprint("admin_inventory", __name__, url_prefix="/inventory")

from . import routes

