import json

import anyio
import httpx
import pytest
from mcp.client.client import Client

from app.main import Receive, Scope, Send, _service_token, create_app, with_service_token
from app.server import build_server

TOKEN = "test-token"


def test_tools_are_listed_and_gateway_status_answers() -> None:
    async def scenario() -> None:
        async with Client(build_server()) as client:
            tools = await client.list_tools()
            assert [t.name for t in tools.tools] == ["gateway_status"]
            result = await client.call_tool("gateway_status", {})
            assert not result.is_error
            assert result.structured_content is not None
            assert result.structured_content["service"] == "data-gateway"
            assert result.structured_content["datasets"] == 0

    anyio.run(scenario)


async def _ok_app(scope: Scope, receive: Receive, send: Send) -> None:
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"inner"})


def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=with_service_token(_ok_app, TOKEN))
    return httpx.AsyncClient(transport=transport, base_url="http://data-gateway:8000")


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer wrong"}, {"Authorization": TOKEN}],
    ids=["no-token", "wrong-token", "no-bearer-prefix"],
)
def test_mcp_rejects_requests_without_service_token(headers: dict[str, str]) -> None:
    async def scenario() -> None:
        async with _client() as client:
            response = await client.post("/mcp", headers=headers, content=b"{}")
            assert response.status_code == 401
            assert json.loads(response.content) == {"error": "unauthorized"}

    anyio.run(scenario)


def test_valid_token_reaches_mcp_and_health_needs_no_token() -> None:
    async def scenario() -> None:
        async with _client() as client:
            ok = await client.post("/mcp", headers={"Authorization": f"Bearer {TOKEN}"})
            assert ok.status_code == 200
            assert ok.content == b"inner"
            health = await client.get("/health")
            assert health.status_code == 200
            assert health.json()["service"] == "data-gateway"

    anyio.run(scenario)


def test_service_refuses_to_start_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATA_GATEWAY_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="DATA_GATEWAY_TOKEN"):
        _service_token()


def test_create_app_builds_with_token() -> None:
    assert callable(create_app(TOKEN))
