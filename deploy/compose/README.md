# Compose

- `compose.dev.yml` — dev-стек: Postgres (ParadeDB), Redis, fake-llm, corp-ext с миграциями и WeKnora
  (`weknora-app`, `weknora-frontend`, `weknora-docreader`; UI — http://localhost:8080, API — http://localhost:8081).
  Образы WeKnora по умолчанию официальные `v0.9.0`; собранные из форка `make weknora-build` подставляются через
  `WEKNORA_IMAGE_PREFIX=corp` и `WEKNORA_VERSION=<тег, который напечатала сборка>`. Модели — fake-llm по `config/weknora/builtin_models.dev.yaml`;
  с `WEKNORA_MODELS_FILE=builtin_models.ollama.yaml` — настоящие `qwen3.5:9b` и `bge-m3` из Ollama на хосте.
  Реранкер в обоих профилях настоящий: сервис `rerank` (TEI на CPU, `BAAI/bge-reranker-v2-m3`, порт 8002);
  веса (~2,3 ГБ) скачиваются с Hugging Face при первом запуске и хранятся в томе `rerank-models`.
  Встроенные агенты — `config/weknora/builtin_agents.yaml` (сразу с моделью).
  Вход в WeKnora — через Keycloak (`keycloak.localhost:8180`, realm `corp`) пользователем mock-AD (`deploy/mock-ad/`).
  `data-gateway` — MCP-каркас на порту 8003.
- `.env.example` — переменные для compose; рабочий `.env` в git не попадает.
- Стек с нуля рядом с рабочим, не трогая его тома: `docker compose -f deploy/compose/compose.dev.yml stop`, затем
  `COMPOSE_PROJECT_NAME=ai-assistant-clean make dev-up` (порты те же — рабочий стек должен быть остановлен).

Дальше: тестовая MS SQL (этап 9);
prod-проекты `weknora`, `app`, `data`, `models/*`, `monitoring` — этап 10 (SPEC §18.2).
