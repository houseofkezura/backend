'''
This module initializes the extensions used in the Flask application.

It sets up SQLAlchemy, Flask-Mail, and Celery with the configurations defined in the Config class.

@author: Emmanuel Olowu
@link: https://github.com/zeddyemy
'''

from flask_cors import CORS
from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_caching import Cache

from .docs import init_docs

from config import Config

cors = CORS()
mail = Mail()
db = SQLAlchemy()
migration = Migrate()
jwt_extended = JWTManager()
app_cache = Cache(config={'CACHE_TYPE': 'flask_caching.backends.SimpleCache'})


def initialize_extensions(app: Flask):
    """Initialize Flask extensions (DB, Mail, Auth, Cache, Migrations, CORS)."""
    db.init_app(app)
    mail.init_app(app)

    jwt_extended.init_app(app)
    app_cache.init_app(app)
    migration.init_app(app, db=db)

    cors.init_app(app=app, resources={r"/*": {"origins": Config.CORS_ORIGINS}}, supports_credentials=True)
