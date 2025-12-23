from flask import Blueprint

bp: Blueprint = Blueprint("web_admin_products", __name__, url_prefix="/products")

from . import routes  # noqa: E402,F401

