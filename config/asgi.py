"""ASGI config para el proyecto.

Daphne expone HTTP y WebSocket en el mismo puerto. ``ProtocolTypeRouter``
deriva cada request según el tipo:

* ``http``  → la app ASGI estándar de Django (DRF, admin, etc.).
* ``websocket`` → ``JWTAuthMiddleware`` valida el token del query string y el
  ``URLRouter`` decide a qué consumer entra.

``AllowedHostsOriginValidator`` rechaza handshakes que no provengan de los
hosts/orígenes permitidos, evitando que cualquier página externa abra un WS
contra esta API.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# get_asgi_application() inicializa Django; debe correr antes de importar
# cualquier cosa que toque modelos (consumers, routing, middleware).
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

from apps.notifications.middleware import JWTAuthMiddleware  # noqa: E402
from apps.notifications.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddleware(URLRouter(websocket_urlpatterns))
        ),
    }
)
