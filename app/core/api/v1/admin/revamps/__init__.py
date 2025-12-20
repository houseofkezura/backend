from flask import Blueprint

bp = Blueprint("admin_revamps", __name__, url_prefix="/revamps")

from . import routes







