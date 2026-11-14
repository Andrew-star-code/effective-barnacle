from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import create_app

TOOLS = [{"type": "function", "function": {"name": "search_knowledge", "parameters": {}}}]


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _user(text: str) -> list[dict[str, Any]]:
    return [{"role": "user", "content": text}]


def _stream(client: TestClient, body: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    chunks: list[dict[str, Any]] = []
    done = False
    with client.stream("POST", "/v1/chat/completions", json={**body, "stream": True}) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue
            data = line.removeprefix("data: ")
            if data == "[DONE]":
                done = True
            else:
                chunks.append(json.loads(data))
    return chunks, done


def _text(chunks: list[dict[str, Any]], key: str) -> str:
    return "".join(c["choices"][0]["delta"].get(key) or "" for c in chunks)


def test_default_non_stream(client: TestClient) -> None:
    response = client.post("/v1/chat/completions", json={"messages": _user("Привет")})
    body = response.json()
    assert body["choices"][0]["message"]["content"] == main.ANSWER
    assert body["usage"]["total_tokens"] > 0


def test_default_stream(client: TestClient) -> None:
    chunks, done = _stream(client, {"messages": _user("Привет")})
    assert done
    assert _text(chunks, "content").strip() == main.ANSWER
    assert chunks[-1]["choices"][0]["finish_reason"] == "stop"


def test_thinking_stream_has_separate_reasoning(client: TestClient) -> None:
    chunks, done = _stream(client, {"messages": _user("[[scenario:thinking]] вопрос")})
    assert done
    assert _text(chunks, "reasoning_content").strip() == main.THINKING
    assert _text(chunks, "content").strip() == main.ANSWER


def test_tool_call_uses_first_tool(client: TestClient) -> None:
    chunks, done = _stream(client, {"messages": _user("[[scenario:tool_call]]"), "tools": TOOLS})
    assert done
    calls = [
        c["choices"][0]["delta"]["tool_calls"]
        for c in chunks
        if "tool_calls" in c["choices"][0]["delta"]
    ]
    assert calls[0][0]["function"]["name"] == "search_knowledge"
    assert chunks[-1]["choices"][0]["finish_reason"] == "tool_calls"


def test_tool_call_named_in_marker(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions",
        json={"messages": _user("[[scenario:tool_call:report_incident]]"), "tools": TOOLS},
    )
    call = response.json()["choices"][0]["message"]["tool_calls"][0]
    assert call["function"]["name"] == "report_incident"


def test_tool_call_without_tools_is_400(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions", json={"messages": _user("[[scenario:tool_call]]"), "stream": True}
    )
    assert response.status_code == 400


def test_after_tool_result_answers_with_text(client: TestClient) -> None:
    messages = [
        *_user("[[scenario:tool_call]]"),
        {"role": "assistant", "content": None, "tool_calls": []},
        {"role": "tool", "tool_call_id": "call_fake_1", "content": "{}"},
    ]
    response = client.post("/v1/chat/completions", json={"messages": messages, "tools": TOOLS})
    assert response.json()["choices"][0]["message"]["content"] == main.AFTER_TOOL


def test_error_500(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions", json={"messages": _user("[[scenario:error_500]]")}
    )
    assert response.status_code == 500


def test_cutoff_stream_has_no_done(client: TestClient) -> None:
    chunks, done = _stream(client, {"messages": _user("[[scenario:cutoff]]")})
    assert not done
    assert all(c["choices"][0]["finish_reason"] is None for c in chunks)


def test_slow_stream_completes(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "SLOW_DELAY_SECONDS", 0.001)
    _, done = _stream(client, {"messages": _user("[[scenario:slow]]")})
    assert done


def test_marker_only_from_last_user_message(client: TestClient) -> None:
    messages = [
        *_user("[[scenario:error_500]]"),
        {"role": "assistant", "content": "ок"},
        *_user("обычный вопрос"),
    ]
    assert client.post("/v1/chat/completions", json={"messages": messages}).status_code == 200


def test_embeddings_are_deterministic(client: TestClient) -> None:
    body = {"input": ["договор поставки", "договор поставки", "приказ"]}
    data = client.post("/v1/embeddings", json=body).json()["data"]
    assert len(data[0]["embedding"]) == main.EMBEDDING_DIM
    assert data[0]["embedding"] == data[1]["embedding"]
    assert data[0]["embedding"] != data[2]["embedding"]
