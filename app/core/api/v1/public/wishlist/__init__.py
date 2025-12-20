from flask import Blueprint

bp = Blueprint("wishlist", __name__, url_prefix="/wishlist")

from . import routes

