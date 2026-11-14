# Compose

- `compose.dev.yml` — dev-стек, часть 1: Postgres (ParadeDB), Redis, fake-llm, corp-ext с миграциями.
- `.env.example` — переменные для compose; рабочий `.env` в git не попадает.

Дальше (этапы 0–1): WeKnora из подмодуля, Keycloak, mock-AD, `embed`/`rerank` на CPU, тестовая MS SQL;
prod-проекты `weknora`, `app`, `data`, `models/*`, `monitoring` — этап 10 (SPEC §18.2).
