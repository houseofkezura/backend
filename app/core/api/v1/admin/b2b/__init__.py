from flask import Blueprint

bp = Blueprint("admin_b2b", __name__, url_prefix="/b2b")

from . import routes

