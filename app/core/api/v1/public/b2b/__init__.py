from flask import Blueprint

bp = Blueprint("b2b", __name__, url_prefix="/b2b")

from . import routes






