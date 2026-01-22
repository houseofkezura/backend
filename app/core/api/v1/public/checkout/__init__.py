from flask import Blueprint

bp = Blueprint("checkout", __name__, url_prefix="/checkout")

from . import routes








