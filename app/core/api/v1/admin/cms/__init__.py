from flask import Blueprint

bp = Blueprint("admin_cms", __name__, url_prefix="/cms")

from . import routes





