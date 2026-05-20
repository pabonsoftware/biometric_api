"""Consumer único para notificaciones push al SPA.

Cada conexión se suscribe a dos grupos:

* ``user.<pk>`` — uno-a-uno, sirve para eventos dirigidos al usuario en
  particular (ej. su agendamiento fue notificado).
* ``staff_supervisors`` — broadcast a roles de supervisión
  (admin/superadmin/coordinador) para ver el flujo operativo en tiempo real.

El productor (Celery task) elige a qué grupos publicar.
"""
from __future__ import annotations

from channels.generic.websocket import AsyncJsonWebsocketConsumer

STAFF_SUPERVISOR_ROLES = frozenset({"admin", "superadmin", "coordinador"})
STAFF_SUPERVISOR_GROUP = "staff_supervisors"


def user_group_name(user_pk: int) -> str:
    return f"user.{user_pk}"


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self) -> None:
        user = self.scope.get("user")
        if user is None or not getattr(user, "is_authenticated", False):
            # 4401: convención de "unauthorized" en WS (close codes 4000–4999 son
            # libres para uso de la aplicación).
            await self.close(code=4401)
            return

        self._user_group = user_group_name(user.pk)
        await self.channel_layer.group_add(self._user_group, self.channel_name)

        self._staff_group: str | None = None
        if getattr(user, "role", None) in STAFF_SUPERVISOR_ROLES:
            self._staff_group = STAFF_SUPERVISOR_GROUP
            await self.channel_layer.group_add(self._staff_group, self.channel_name)

        await self.accept()

    async def disconnect(self, code) -> None:  # noqa: ANN001
        user_group = getattr(self, "_user_group", None)
        if user_group:
            await self.channel_layer.group_discard(user_group, self.channel_name)
        staff_group = getattr(self, "_staff_group", None)
        if staff_group:
            await self.channel_layer.group_discard(staff_group, self.channel_name)

    async def notification_message(self, event: dict) -> None:
        # El productor envía {"type": "notification.message", "payload": {...}};
        # acá lo serializamos tal cual al cliente.
        await self.send_json(event["payload"])
