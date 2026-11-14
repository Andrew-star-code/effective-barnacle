"""fake-llm: OpenAI-совместимый сервер со сценариями ответа (SPEC §18.1).

Сценарий выбирается маркером в последнем сообщении пользователя:
``[[scenario:<имя>]]`` или ``[[scenario:tool_call:<имя_инструмента>]]``.

Сценарии:
- ``default``   — обычный ответ (стрим или целиком);
- ``thinking``  — размышления в ``reasoning_content``, затем ответ;
- ``tool_call`` — вызов инструмента (указанного в маркере либо первого из ``tools``);
  после сообщения ``role=tool`` отвечает текстом, чтобы цикл агента завершался;
- ``mcp:<инструмент>`` — вызов MCP-инструмента через каталог WeKnora: ``discover_mcp_tools``
  (``list_servers``, затем ``describe``) и ``call_mcp_tool``; ``server_id`` и ``tool_ref`` берутся
  из ответов WeKnora, после третьего результата — текст;
- ``error_500`` — HTTP 500;
- ``cutoff``    — стрим обрывается без ``[DONE]``;
- ``slow``      — стрим с задержкой между чанками.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict

SCENARIO_RE = re.compile(r"\[\[scenario:([a-z0-9_]+)(?::([A-Za-z0-9_.\-]+))?\]\]")
EMBEDDING_DIM = 1024
SLOW_DELAY_SECONDS = 0.5

ANSWER = "Это тестовый ответ fake-llm."
THINKING = "Пользователь прислал тестовый запрос. Отвечаю коротко."
AFTER_TOOL = "Инструмент вернул результат, задача выполнена."
AFTER_MCP = "MCP-инструмент вызван, результат получен."

# Служебные инструменты WeKnora для MCP по требованию (internal/agent/tools/definitions.go).
DISCOVER_MCP = "discover_mcp_tools"
CALL_MCP = "call_mcp_tool"
SERVER_ID_RE = re.compile(r'"server_id"\s*:\s*"([^"]+)"')
TOOL_REF_RE = re.compile(r'"tool_ref"\s*:\s*"([^"]+)"')


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str = "fake"
    messages: list[dict[str, Any]]
    stream: bool = False
    tools: list[dict[str, Any]] | None = None


class EmbeddingRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str = "fake-embed"
    input: str | list[str]


def _text_of(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
    return ""


def pick_scenario(messages: list[dict[str, Any]]) -> tuple[str, str | None]:
    """Маркер ищется в последнем сообщении пользователя.

    На tool-результат отвечает текстом (``after_tool``), кроме сценария ``mcp``: там цепочка
    вызовов продолжается, пока не пройдены все шаги.
    """
    scenario: tuple[str, str | None] = ("default", None)
    for message in reversed(messages):
        if message.get("role") == "user":
            match = SCENARIO_RE.search(_text_of(message))
            if match:
                scenario = (match.group(1), match.group(2))
            break
    if messages and messages[-1].get("role") == "tool" and scenario[0] != "mcp":
        return "after_tool", None
    return scenario


def _tool_results_since_user(messages: list[dict[str, Any]]) -> list[str]:
    results: list[str] = []
    for message in reversed(messages):
        role = message.get("role")
        if role == "user":
            break
        if role == "tool":
            results.append(_text_of(message))
    return list(reversed(results))


def plan_mcp_step(messages: list[dict[str, Any]], tool: str) -> tuple[str, dict[str, Any]] | str:
    """Следующий шаг сценария ``mcp``: (инструмент, аргументы) или итоговый текст."""
    results = _tool_results_since_user(messages)
    if not results:
        return DISCOVER_MCP, {"mode": "list_servers"}
    if len(results) == 1:
        server = SERVER_ID_RE.search(results[0])
        if not server:
            return "fake-llm: в ответе list_servers нет server_id"
        return DISCOVER_MCP, {"mode": "describe", "server_id": server.group(1), "tool_name": tool}
    if len(results) == 2:
        ref = TOOL_REF_RE.search(results[1])
        if not ref:
            return f"fake-llm: в ответе describe нет tool_ref для {tool}"
        return CALL_MCP, {"tool_ref": ref.group(1), "arguments": {}}
    return AFTER_MCP


def _tool_name(request: ChatRequest, requested: str | None) -> str:
    if requested:
        return requested
    if request.tools:
        return str(request.tools[0].get("function", {}).get("name", "unknown_tool"))
    raise HTTPException(status_code=400, detail="tool_call scenario requires tools or a tool name")


def _chunk(model: str, delta: dict[str, Any], finish: str | None = None) -> str:
    payload = {
        "id": "chatcmpl-fake",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _usage(prompt: list[dict[str, Any]], completion: str) -> dict[str, int]:
    prompt_tokens = sum(len(_text_of(m).split()) for m in prompt)
    completion_tokens = len(completion.split())
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }


def _tool_call(
    name: str, arguments: dict[str, Any] | None = None, call_no: int = 1
) -> dict[str, Any]:
    return {
        "index": 0,
        "id": f"call_fake_{call_no}",
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments or {}, ensure_ascii=False)},
    }


def _next_action(request: ChatRequest, scenario: str, arg: str | None) -> dict[str, Any] | str:
    """Что ответить: вызов инструмента (словарь tool_call) или текст."""
    if scenario == "tool_call":
        return _tool_call(_tool_name(request, arg))
    if scenario == "mcp":
        step = plan_mcp_step(request.messages, arg or "")
        if isinstance(step, str):
            return step
        call_no = len(_tool_results_since_user(request.messages)) + 1
        return _tool_call(step[0], step[1], call_no)
    return AFTER_TOOL if scenario == "after_tool" else ANSWER


async def _stream(request: ChatRequest, scenario: str, arg: str | None) -> AsyncIterator[str]:
    model = request.model
    delay = SLOW_DELAY_SECONDS if scenario == "slow" else 0.0
    yield _chunk(model, {"role": "assistant", "content": ""})

    action = _next_action(request, scenario, arg)
    if isinstance(action, dict):
        yield _chunk(model, {"tool_calls": [action]})
        yield _chunk(model, {}, finish="tool_calls")
        yield "data: [DONE]\n\n"
        return

    if scenario == "thinking":
        for word in THINKING.split():
            yield _chunk(model, {"reasoning_content": word + " "})

    text = action
    words = text.split()
    for index, word in enumerate(words):
        if scenario == "cutoff" and index == len(words) // 2:
            return  # обрыв: без finish_reason и [DONE]
        if delay:
            await asyncio.sleep(delay)
        yield _chunk(model, {"content": word + " "})

    yield _chunk(model, {}, finish="stop")
    yield "data: [DONE]\n\n"


def _complete(request: ChatRequest, scenario: str, arg: str | None) -> dict[str, Any]:
    action = _next_action(request, scenario, arg)
    message: dict[str, Any] = {"role": "assistant", "content": action}
    finish = "stop"
    if isinstance(action, dict):
        message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{k: v for k, v in action.items() if k != "index"}],
        }
        finish = "tool_calls"
    elif scenario == "thinking":
        message["reasoning_content"] = THINKING
    return {
        "id": "chatcmpl-fake",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{"index": 0, "message": message, "finish_reason": finish}],
        "usage": _usage(request.messages, str(message.get("content") or "")),
    }


def _embedding(text: str) -> list[float]:
    """Детерминированный псевдовектор: одинаковый текст — одинаковый вектор."""
    values: list[float] = []
    counter = 0
    while len(values) < EMBEDDING_DIM:
        digest = hashlib.sha256(f"{counter}:{text}".encode()).digest()
        values.extend((byte - 127.5) / 127.5 for byte in digest)
        counter += 1
    return values[:EMBEDDING_DIM]


def create_app() -> FastAPI:
    app = FastAPI(title="fake-llm", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/models")
    async def models() -> dict[str, Any]:
        return {
            "object": "list",
            "data": [{"id": name, "object": "model"} for name in ("fake", "fake-embed")],
        }

    @app.post("/v1/chat/completions", response_model=None)
    async def chat(request: ChatRequest) -> JSONResponse | StreamingResponse:
        scenario, arg = pick_scenario(request.messages)
        if scenario == "error_500":
            raise HTTPException(status_code=500, detail="fake-llm: scenario error_500")
        if scenario == "tool_call":
            _tool_name(request, arg)  # 400 до начала стрима, а не посреди него
        if scenario == "mcp" and not arg:
            raise HTTPException(status_code=400, detail="mcp scenario requires a tool name")
        if request.stream:
            return StreamingResponse(
                _stream(request, scenario, arg), media_type="text/event-stream"
            )
        if scenario == "slow":
            await asyncio.sleep(SLOW_DELAY_SECONDS)
        return JSONResponse(_complete(request, scenario, arg))

    @app.post("/v1/embeddings")
    async def embeddings(request: EmbeddingRequest) -> dict[str, Any]:
        inputs = [request.input] if isinstance(request.input, str) else request.input
        return {
            "object": "list",
            "model": request.model,
            "data": [
                {"object": "embedding", "index": i, "embedding": _embedding(text)}
                for i, text in enumerate(inputs)
            ],
            "usage": {"prompt_tokens": 0, "total_tokens": 0},
        }

    return app


app = create_app()
