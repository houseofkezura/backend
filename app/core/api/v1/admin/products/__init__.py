from flask import Blueprint

bp = Blueprint("admin_products", __name__, url_prefix="/products")

from . import routes







