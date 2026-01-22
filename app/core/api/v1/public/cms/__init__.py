from flask import Blueprint

bp = Blueprint("cms", __name__, url_prefix="/cms")

from . import routes








