"""
Settings de desarrollo local.
"""
from .base import *  # noqa: F401,F403
from .base import INSTALLED_APPS, MIDDLEWARE

DEBUG = True

# Debug toolbar (opcional, solo si está instalado)
try:
    import debug_toolbar  # noqa: F401

    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        *MIDDLEWARE,
    ]
    INTERNAL_IPS = ["127.0.0.1", "localhost"]
except ImportError:
    pass

# En dev permitimos cualquier origen para no bloquear pruebas con frontend local
CORS_ALLOW_ALL_ORIGINS = True
