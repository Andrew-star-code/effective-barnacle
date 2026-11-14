# Changelog

Изменения по версиям, включая версию WeKnora (SPEC §19.1).

## Не выпущено

База WeKnora: тег `v0.9.0` (коммит `f17ee8a8`).

### Добавлено

- ТЗ v2 на базе WeKnora — `docs/SPEC.md`.
- Каркас монорепозитория: подмодуль `weknora/`, Makefile, git-хуки, dev-compose (Postgres/ParadeDB, Redis, fake-llm, corp-ext).
- `corp-ext`: конфигурация с валидацией, JSON-логи, `/health`, `/metrics`, Alembic для схемы `corp`, CLI.
- `fake-llm`: OpenAI-совместимый mock со сценариями ответа.
- `corp-admin`: каркас SPA (роутинг, layout, TDesign, i18n, клиент API из OpenAPI).
- Документация: AGENTS.md, ADR 0001–0012, реестр патчей, статус с вопросами к плану и пунктами пилота.
- ADR 0013–0016.
- Правила написания кода для агента и людей: `docs/guides/coding.md`, выжимка в `AGENTS.md`.
- `corp-ext`: реестр моделей `app/core/model_registry.py` с тестом — новые таблицы не теряются для Alembic.
- Dev-стек: WeKnora `v0.9.0` (`weknora-app`, `weknora-frontend`, `weknora-docreader`) в `compose.dev.yml`, UI на `localhost:8080`;
  каталоги моделей `config/weknora/builtin_models.dev.yaml` (fake-llm) и `builtin_models.ollama.yaml`
  (`qwen3.5:9b` и `bge-m3` из Ollama на машине разработчика), переключение — `WEKNORA_MODELS_FILE`.
- Dev-стек: реранкер `BAAI/bge-reranker-v2-m3` на CPU (сервис `rerank`, Hugging Face TEI `cpu-1.9.2`).
- P-01: SQL русского BM25-индекса (`stemmer=russian`, русские стоп-слова, нижний регистр) —
  `services/corp-ext/app/modules/provisioning/sql/search_index.sql`, проверен на dev-стеке.

### Исправлено

- Профиль Ollama: размышления `qwen3.5` выключаются (`reasoning_effort: none`); без этого служебные
  генерации WeKnora при индексации возвращали пустой ответ.

### Изменено

- SPEC, ревизия 2.1 (решения 26–32): закреплён тег `v0.9.0`; guard-модель — первая линия модерации, скрытый репорт и P-04 — после запуска; русский BM25-индекс ставится шагом `provision --search-index`; чат-эндпоинты идут через прокси `corp-ext`; смена email отслеживается по `objectGUID`; блок-лист IP проверяется в `auth_request`; taskiq вместо Celery.
- Подмодуль `weknora/` переключён с `cbdcebab` на тег `v0.9.0`.
