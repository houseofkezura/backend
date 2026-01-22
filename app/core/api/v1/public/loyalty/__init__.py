from flask import Blueprint

bp = Blueprint("loyalty", __name__, url_prefix="/loyalty")

from . import routes







