from flask import Blueprint

bp: Blueprint = Blueprint("categories", __name__, url_prefix="/products/categories")

from . import routes  # noqa: E402,F401

