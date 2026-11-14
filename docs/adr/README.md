# ADR — архитектурные решения

Новое значимое решение (в том числе каждый новый патч WeKnora) — новый файл `NNNN-<slug>.md`:
контекст, решение, отвергнутые альтернативы, последствия.

| № | Решение |
| --- | --- |
| 0001 | [Основа — WeKnora (MIT)](0001-weknora-base.md) |
| 0002 | [WeKnora без глубокого форка: закреплённая версия, реестр патчей, свои сервисы рядом](0002-weknora-no-deep-fork.md) |
| 0003 | [Вход — Keycloak с федерацией AD, в WeKnora — OIDC](0003-keycloak-oidc.md) |
| 0004 | [Права на базы — через пространства и организации WeKnora](0004-access-via-workspaces.md) |
| 0005 | [Поиск — PostgreSQL + ParadeDB, а не Qdrant](0005-paradedb-not-qdrant.md) |
| 0006 | [Свой код — Python, своя админка — Vue 3 + TDesign](0006-python-and-vue-for-own-code.md) |
| 0007 | [Корпоративные инструменты — встроенные MCP-сервисы WeKnora](0007-builtin-mcp-tools.md) |
| 0008 | [Лимиты — прокси чат-эндпоинтов в corp-ext и auth_request в nginx](0008-limits-auth-request.md) |
| 0009 | [Генерация файлов к запуску — MCP-инструменты corp-files, песочница — после запуска](0009-file-generation-via-mcp.md) |
| 0010 | [vLLM для всех моделей](0010-vllm-for-all-models.md) |
| 0011 | [LiteLLM Proxy только для разработчиков](0011-litellm-for-developers.md) |
| 0012 | [JWT WeKnora в localStorage — принятое отступление](0012-jwt-in-localstorage.md) |
| 0013 | [Модерация: guard-модель — первая линия, скрытый репорт — после запуска](0013-guard-first-hidden-report-later.md) |
| 0014 | [Русский BM25-индекс — шагом provision, а не миграцией в форке](0014-bm25-index-outside-migrations.md) |
| 0015 | [Фоновые задачи — taskiq](0015-taskiq-for-background-jobs.md) |
| 0016 | [Сотрудник опознаётся по objectGUID, смена email переносится в WeKnora](0016-user-identity-by-objectguid.md) |
