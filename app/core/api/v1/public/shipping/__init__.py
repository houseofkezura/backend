from flask import Blueprint

bp = Blueprint("shipping", __name__, url_prefix="/shipping")

from . import routes




