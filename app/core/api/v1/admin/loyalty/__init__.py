from flask import Blueprint

bp = Blueprint("admin_loyalty", __name__, url_prefix="/loyalty")

from . import routes






