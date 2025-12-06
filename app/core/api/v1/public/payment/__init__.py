from flask import Blueprint

bp: Blueprint = Blueprint("api_v1_payment", __name__, url_prefix="/payment")

from . import routes as payment_routes


