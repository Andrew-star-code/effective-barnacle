# fake-llm

OpenAI-совместимый mock для тестов без GPU (SPEC §18.1): `/v1/chat/completions` (стрим и целиком),
`/v1/embeddings` (детерминированные векторы на 1024 измерения), `/v1/models`, `/health`.

Сценарий выбирается маркером в последнем сообщении пользователя, поэтому e2e-тесты детерминированы:

| Маркер | Поведение |
| --- | --- |
| нет маркера | обычный ответ |
| `[[scenario:thinking]]` | размышления в `reasoning_content`, затем ответ |
| `[[scenario:tool_call]]` | вызов первого инструмента из `tools` |
| `[[scenario:tool_call:report_incident]]` | вызов указанного инструмента (в том числе MCP) |
| `[[scenario:error_500]]` | HTTP 500 |
| `[[scenario:cutoff]]` | стрим обрывается без `[DONE]` |
| `[[scenario:slow]]` | медленный стрим |

После сообщения `role=tool` модель всегда отвечает текстом — цикл агента завершается.

```bash
uv sync && uv run pytest
uv run uvicorn app.main:app --port 8001
```

Не реализовано: `/rerank` (в dev реранкер — настоящая модель на CPU, SPEC §18.1).
