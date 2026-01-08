# Apache Superset Configuration
# Phase 3: Enterprise BI Platform Integration
#
# This configuration enables Superset to:
# - Connect to our SQL Server database
# - Use Redis for caching (shared with main app)
# - Allow embedding in iframes (React integration)
# - Match our application's theme

import os

# Basic config
ROW_LIMIT = 5000
SUPERSET_WEBSERVER_PORT = 8088

# Secret key - MUST be set in production
SECRET_KEY = os.environ.get(
    "SUPERSET_SECRET_KEY", "localllm_default_secret_key_change_me_in_production"
)

# Database for Superset metadata (NOT the analytics data)
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:////app/superset_home/superset.db"
)

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = []
WTF_CSRF_TIME_LIMIT = 60 * 60 * 24 * 365

# Session configuration
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
SESSION_COOKIE_HTTPONLY = True

# Enable iframe embedding
PUBLIC_ROLE_LIKE = "Gamma"
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": [
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
}

# Allow embedding in iframes
HTTP_HEADERS = {"X-Frame-Options": "ALLOWALL"}
TALISMAN_ENABLED = False

# Feature flags
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_NATIVE_FILTERS_SET": True,
    "ALERT_REPORTS": True,
    "EMBEDDED_SUPERSET": True,
    "EMBEDDABLE_CHARTS": True,
}

# SQL Lab configuration
SQLLAB_TIMEOUT = 300
SQLLAB_DEFAULT_DBID = 1

# Cache configuration (using Redis - different DB from main app)
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_HOST": os.environ.get("REDIS_HOST", "redis-stack"),
    "CACHE_REDIS_PORT": int(os.environ.get("REDIS_PORT", 6379)),
    "CACHE_REDIS_DB": 1,  # Use different DB than main app
}

FILTER_STATE_CACHE_CONFIG = CACHE_CONFIG
EXPLORE_FORM_DATA_CACHE_CONFIG = CACHE_CONFIG

# Logging
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"
LOG_LEVEL = os.environ.get("SUPERSET_LOG_LEVEL", "INFO")

# Theming (match our app's look)
THEME_OVERRIDES = {
    "borderRadius": 4,
    "colors": {
        "primary": {
            "base": "rgb(59, 130, 246)",  # Blue-500
        },
        "secondary": {
            "base": "rgb(100, 116, 139)",  # Slate-500
        },
    },
}
