"""Development settings."""
from .base import *  # noqa: F401,F403
from .base import INSTALLED_APPS, LOGGING

DEBUG = True
INSTALLED_APPS += ["django_extensions"]

# Permissive CORS in dev
CORS_ALLOW_ALL_ORIGINS = True

LOGGING["root"]["level"] = "DEBUG"

# drf-spectacular: expose the schema browsably
SPECTACULAR_SETTINGS = {**globals().get("SPECTACULAR_SETTINGS", {}), "SERVE_INCLUDE_SCHEMA": True}
