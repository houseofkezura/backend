from flask import Blueprint

bp = Blueprint("revamps", __name__, url_prefix="/revamps")

from . import routes




