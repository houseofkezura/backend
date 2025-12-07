from flask import Blueprint

bp = Blueprint("addresses", __name__, url_prefix="/me/addresses")

from . import routes

