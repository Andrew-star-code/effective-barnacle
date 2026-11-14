# Compose

- `compose.dev.yml` — dev-стек: Postgres (ParadeDB), Redis, fake-llm, corp-ext с миграциями и WeKnora
  (`weknora-app`, `weknora-frontend`, `weknora-docreader`; UI — http://localhost:8080, API — http://localhost:8081).
  Образы WeKnora пока официальные `v0.9.0`; после `make weknora-build` подставляются через
  `WEKNORA_IMAGE_PREFIX` и `WEKNORA_VERSION`. Модели — fake-llm по `config/weknora/builtin_models.dev.yaml`;
  с `WEKNORA_MODELS_FILE=builtin_models.ollama.yaml` — настоящие `qwen3.5:9b` и `bge-m3` из Ollama на хосте.
  До Keycloak (этап 1) вход в WeKnora — регистрацией.
- `.env.example` — переменные для compose; рабочий `.env` в git не попадает.

Дальше (этапы 0–1): образы WeKnora из форка, Keycloak, mock-AD, `embed`/`rerank` на CPU, тестовая MS SQL;
prod-проекты `weknora`, `app`, `data`, `models/*`, `monitoring` — этап 10 (SPEC §18.2).
