"""Tests del WebSocket consumer.

Usamos ``InMemoryChannelLayer`` para no depender de Redis. El handshake JWT
se prueba pasando el access token en el query string, igual que lo hace el
cliente del SPA.
"""
from __future__ import annotations

import pytest
from channels.testing import WebsocketCommunicator
from django.test import override_settings
from rest_framework_simplejwt.tokens import AccessToken

from apps.notifications.consumers import (
    STAFF_SUPERVISOR_GROUP,
    NotificationConsumer,
    user_group_name,
)
from apps.notifications.middleware import JWTAuthMiddleware
from apps.users.tests.factories import (
    AdminFactory,
    CoordinadorFactory,
    IngenieroFactory,
    SuperadminFactory,
    TecnicoFactory,
)

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.asyncio,
    override_settings(
        CHANNEL_LAYERS={
            "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
        }
    ),
]


def _build_communicator(token: str | None) -> WebsocketCommunicator:
    path = "/ws/notifications/"
    if token is not None:
        path = f"{path}?token={token}"
    application = JWTAuthMiddleware(NotificationConsumer.as_asgi())
    return WebsocketCommunicator(application, path)


def _access_for(user) -> str:
    return str(AccessToken.for_user(user))


class TestNotificationConsumerAuth:
    async def test_rejects_connection_without_token(self):
        communicator = _build_communicator(token=None)
        connected, code = await communicator.connect()
        assert connected is False
        assert code == 4401

    async def test_rejects_connection_with_invalid_token(self):
        communicator = _build_communicator(token="not-a-real-token")
        connected, code = await communicator.connect()
        assert connected is False
        assert code == 4401

    async def test_accepts_connection_with_valid_token(self):
        user = await _afactory(TecnicoFactory)
        communicator = _build_communicator(token=_access_for(user))
        connected, _ = await communicator.connect()
        assert connected is True
        await communicator.disconnect()


class TestNotificationConsumerDispatch:
    async def test_receives_message_on_user_group(self):
        user = await _afactory(IngenieroFactory)
        communicator = _build_communicator(token=_access_for(user))
        connected, _ = await communicator.connect()
        assert connected is True

        await _group_send(
            user_group_name(user.pk),
            {"foo": "bar", "schedule_id": 42},
        )

        received = await communicator.receive_json_from()
        assert received == {"foo": "bar", "schedule_id": 42}
        await communicator.disconnect()

    @pytest.mark.parametrize(
        "factory",
        [AdminFactory, SuperadminFactory, CoordinadorFactory],
    )
    async def test_supervisor_roles_join_staff_group(self, factory):
        user = await _afactory(factory)
        communicator = _build_communicator(token=_access_for(user))
        connected, _ = await communicator.connect()
        assert connected is True

        await _group_send(STAFF_SUPERVISOR_GROUP, {"hello": "supervisors"})

        received = await communicator.receive_json_from()
        assert received == {"hello": "supervisors"}
        await communicator.disconnect()

    async def test_non_supervisor_does_not_join_staff_group(self):
        user = await _afactory(TecnicoFactory)
        communicator = _build_communicator(token=_access_for(user))
        connected, _ = await communicator.connect()
        assert connected is True

        await _group_send(STAFF_SUPERVISOR_GROUP, {"hello": "supervisors"})

        # Sin mensaje en el canal del técnico no asignado.
        assert await communicator.receive_nothing(timeout=0.2) is True
        await communicator.disconnect()


# ----- helpers asíncronos -----------------------------------------------------


async def _afactory(factory):
    """factory_boy es síncrono; lo trasladamos al thread pool."""
    from asgiref.sync import sync_to_async

    return await sync_to_async(factory)()


async def _group_send(group: str, payload: dict) -> None:
    from channels.layers import get_channel_layer

    layer = get_channel_layer()
    await layer.group_send(
        group,
        {"type": "notification.message", "payload": payload},
    )
