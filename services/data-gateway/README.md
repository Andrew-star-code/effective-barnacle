# data-gateway

Семантический слой над SQL-БД: каталог, функции, контролируемый text-to-SQL; встроенный MCP-сервис WeKnora (SPEC §10.5).

Статус: каркас (этап 0); наполнение — этап 9.

## Что есть

- MCP-сервер по Streamable HTTP на `/mcp` (`app/server.py`, `app/main.py`), stateless.
- Доступ — только с `Authorization: Bearer <DATA_GATEWAY_TOKEN>`; без токена сервис не стартует. `/health` — без токена.
- Один служебный инструмент `gateway_status`: версия и число наборов данных в каталоге; пользовательских данных не отдаёт.

Подключение в WeKnora (dev): MCP-сервис с транспортом `http-streamable`, URL `http://data-gateway:8000/mcp`,
заголовок `Authorization: Bearer <DATA_GATEWAY_TOKEN>`. Проверено запуском 14.11.2026: сценарий fake-llm
`[[scenario:mcp:gateway_status]]` и `qwen3.5:9b` вызывают инструмент через WeKnora.

## Планируемый состав (этап 9)

- `catalog/sources.yaml`
- `catalog/datasets/*.yaml`
- `catalog/functions/*.yaml`
- подпись пользователя `X-Corp-User` (P-03, этап 4) для инструментов с данными
