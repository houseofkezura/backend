from flask import Blueprint

bp = Blueprint("materials", __name__, url_prefix="/materials")

from . import routes
