"""ASGI-приложение data-gateway: Streamable HTTP MCP за статическим токеном сервиса (SPEC §10.1)."""

import hmac
import os
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from mcp.server.transport_security import TransportSecuritySettings

from app.server import build_server

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

# Имена, под которыми сервис вызывают из сети Docker и с хоста (проверка заголовка Host).
ALLOWED_HOSTS = ["data-gateway:*", "localhost:*", "127.0.0.1:*"]


def _service_token() -> str:
    token = os.environ.get("DATA_GATEWAY_TOKEN", "").strip()
    if not token:
        raise RuntimeError("DATA_GATEWAY_TOKEN не задан: data-gateway без токена не запускается")
    return token


async def _send_json(send: Send, status: int, body: bytes) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": body})


def with_service_token(app: ASGIApp, token: str) -> ASGIApp:
    """Пускает к MCP только с `Authorization: Bearer <токен сервиса>`; `/health` — без токена."""
    expected = f"Bearer {token}".encode()

    async def guarded(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await app(scope, receive, send)
            return
        if scope["path"] == "/health":
            await _send_json(send, 200, b'{"status":"ok","service":"data-gateway"}')
            return
        headers = dict(scope.get("headers") or [])
        if not hmac.compare_digest(headers.get(b"authorization", b""), expected):
            await _send_json(send, 401, b'{"error":"unauthorized"}')
            return
        await app(scope, receive, send)

    return guarded


def create_app(token: str) -> ASGIApp:
    mcp_app = build_server().streamable_http_app(
        stateless_http=True,
        transport_security=TransportSecuritySettings(allowed_hosts=ALLOWED_HOSTS),
    )
    return with_service_token(mcp_app, token)


def app_factory() -> ASGIApp:
    """Точка входа uvicorn (`--factory`): токен читается при старте, без него сервис падает."""
    return create_app(_service_token())
