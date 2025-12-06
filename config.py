import os, logging


class PaymentConfig:
    PAYMENT_GATEWAY = os.getenv("PAYMENT_GATEWAY")
    PAYMENT_GATEWAY_API_KEY = os.getenv("PAYMENT_GATEWAY_API_KEY")
    PAYMENT_GATEWAY_SECRET_KEY = os.getenv("PAYMENT_GATEWAY_SECRET_KEY")
    PAYMENT_GATEWAY_PUBLIC_KEY = os.getenv("PAYMENT_GATEWAY_PUBLIC_KEY")
    PAYMENT_GATEWAY_TEST_MODE = os.getenv("PAYMENT_GATEWAY_TEST_MODE")
    PAYMENT_GATEWAY_TEST_API_KEY = os.getenv("PAYMENT_GATEWAY_TEST_API_KEY")
    PAYMENT_GATEWAY_TEST_SECRET_KEY = os.getenv("PAYMENT_GATEWAY_TEST_SECRET_KEY")
    PAYMENT_GATEWAY_TEST_PUBLIC_KEY = os.getenv("PAYMENT_GATEWAY_TEST_PUBLIC_KEY")


class Config(PaymentConfig):
    # Environment
    ENV = os.getenv("ENV") or "development"
    DEBUG = (ENV == "development")  # Enable debug mode only in development
    SECRET_KEY = os.getenv("SECRET_KEY") or os.environ.get("SECRET_KEY")
    EMERGENCY_MODE = os.getenv("EMERGENCY_MODE") or os.environ.get("EMERGENCY_MODE") or False
    

    # Static and template folders
    STATIC_FOLDER = "resources/static"
    TEMPLATE_FOLDER = "resources/templates"
    
    # CORS
    CORS_ORIGINS = os.getenv("CLIENT_ORIGINS", "http://localhost:3000,http://localhost:5173")
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS.split(",")]
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SEED_DB = os.getenv("SEED_DB") or False
    DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD")
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    BASE_LOG_LEVEL = os.getenv("BASE_LOG_LEVEL", "WARNING")
    
    # JWT configurations
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    
    # Domains
    APP_DOMAIN = os.getenv("APP_DOMAIN") or "http://localhost:3000"
    API_DOMAIN = os.getenv("API_DOMAIN") or "http://localhost:5050"
    
    # mail configurations
    MAIL_SERVER = os.getenv("MAIL_SERVER") or 'smtp.gmail.com'
    MAIL_PORT = os.getenv("MAIL_PORT") or 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    MAIL_ALIAS = (f"{MAIL_DEFAULT_SENDER}", f"{MAIL_USERNAME}")
    
    # Cloudinary configurations
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    
    # eSIM Aggregator configurations
    USE_MOCK = os.getenv("USE_MOCK", "false").lower() in ("true", "1", "yes")
    ESIM_AGGREGATOR = os.getenv("ESIM_AGGREGATOR", "zendit").lower()  # Options: "zendit", "mock"
    
    # Zendit-specific configurations
    ZENDIT_API_URL = os.getenv("ZENDIT_API_URL") or "https://test-api.zendit.io/v1"
    ZENDIT_API_KEY = os.getenv("ZENDIT_API_KEY")
    
    # Legacy/fallback aggregator configs (for backward compatibility)
    ESIM_AGGREGATOR_API_URL = os.getenv("ESIM_AGGREGATOR_API_URL") or ZENDIT_API_URL
    ESIM_AGGREGATOR_API_KEY = os.getenv("ESIM_AGGREGATOR_API_KEY") or ZENDIT_API_KEY
    
    ESIM_OFFERS_CACHE_TTL = int(os.getenv("ESIM_OFFERS_CACHE_TTL", "3600"))  # 1 hour default
    
    # ExchangeRate-API
    EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
    EXCHANGE_RATE_API_URL = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest"
    
    # Currency conversion settings
    CURRENCY_MARKUP_PERCENTAGE = float(os.getenv("CURRENCY_MARKUP_PERCENTAGE", "0.0"))  # Optional markup (e.g., 3.0 for 3%)
    DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "NGN")  # Default currency for display

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or "sqlite:///db.sqlite3"

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# Map config based on environment
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}
