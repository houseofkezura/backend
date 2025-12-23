from flask import Blueprint

bp: Blueprint = Blueprint("prod_cats", __name__, url_prefix="/categories")

from . import controllers, routes  # noqa: E402,F401

