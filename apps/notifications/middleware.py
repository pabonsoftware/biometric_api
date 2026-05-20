"""Middleware ASGI que autentica el handshake WebSocket vía JWT.

El token de acceso viaja en el query string (`?token=<access>`) porque los
navegadores no permiten setear cabeceras `Authorization` en `new WebSocket()`.
La validación reutiliza la misma `AccessToken` de SimpleJWT que usa la API REST,
por lo que un mismo token sirve para ambos canales mientras viva.
"""
from __future__ import annotations

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _get_user(user_id: int):
    User = get_user_model()
    try:
        return User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope["user"] = await self._resolve_user(scope)
        return await super().__call__(scope, receive, send)

    async def _resolve_user(self, scope):
        query_string = scope.get("query_string", b"").decode("utf-8")
        token = parse_qs(query_string).get("token", [None])[0]
        if not token:
            return AnonymousUser()
        try:
            validated = AccessToken(token)
        except (InvalidToken, TokenError):
            return AnonymousUser()
        user_id = validated.get("user_id")
        if not user_id:
            return AnonymousUser()
        return await _get_user(user_id)
