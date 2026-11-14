# corp-ext

Корпоративный слой рядом с WeKnora (SPEC §2.1): синхронизация AD и раскладка по пространствам,
профиль, лимиты, инциденты, модерация, выгрузки, API для `corp-admin`, встроенные MCP-сервисы.

Сейчас это каркас этапа 0: конфиг с валидацией, JSON-логи, `/health`, `/metrics`, Alembic для схемы `corp`.

```bash
uv sync                                   # зависимости по uv.lock
uv run pytest                             # тесты
uv run uvicorn app.main:app_factory --factory --reload
uv run python -m app.cli config check     # проверка конфигурации
uv run alembic upgrade head               # миграции схемы corp
```

- Конфиг: `CORP_EXT_CONFIG` (YAML) + переменные `CORP_EXT_*` (вложенность через `__`). Пример — `config/corp-ext.example.yaml`.
- Модули — `app/modules/*`, у каждого свой README по шаблону SPEC §19.3.
- В таблицы WeKnora сервис не пишет (исключения — SPEC §16.2); читает их только через `app/modules/weknora`.
