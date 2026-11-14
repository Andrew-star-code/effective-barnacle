# Корпоративный ИИ-ассистент

Веб-чат с RAG для сотрудников и API моделей для разработчиков в закрытом контуре.
Основа — [WeKnora](https://github.com/Tencent/WeKnora) (подмодуль `weknora/`), рядом — свои сервисы.

- Требования: [docs/SPEC.md](docs/SPEC.md)
- Правила и карта проекта: [AGENTS.md](AGENTS.md)
- Прогресс и открытые вопросы: [docs/status.md](docs/status.md)
- Вся документация: [docs/README.md](docs/README.md)

## Быстрый старт

Нужны `git`, `bash`, `make`, [`uv`](https://docs.astral.sh/uv/), Node 22 с `pnpm`, Docker.
На Windows работайте из WSL2 (Ubuntu): Makefile и хуки рассчитаны на Linux-оболочку.

```bash
git clone --recurse-submodules <адрес репозитория> ai-assistant && cd ai-assistant
make install                 # зависимости по lock-файлам и git-хуки
SKIP_IMAGES=1 make check     # линт, типы, тесты, сборка фронтенда, проверка документации
make dev-up                  # Postgres (ParadeDB), Redis, fake-llm, corp-ext
```

После `make dev-up`: `corp-ext` — <http://localhost:8000/health> (OpenAPI — `/corp/api/docs`),
`fake-llm` — <http://localhost:8001/v1/models>. Админка: `cd services/corp-admin && pnpm dev`.

Сейчас проект на этапе 0 (каркас): WeKnora, Keycloak и mock-AD в dev-стек ещё не включены — см. [docs/status.md](docs/status.md).

## Состав

| Каталог | Что это |
| --- | --- |
| `weknora/` | подмодуль с WeKnora; правки — только патчами из [реестра](docs/patches.md) |
| `services/corp-ext/` | синхронизация AD, пространства, лимиты, инциденты, MCP-сервисы (Python, FastAPI) |
| `services/corp-admin/` | админка для разделов, которых нет в WeKnora (Vue 3 + TDesign) |
| `services/data-gateway/` | семантический слой над SQL-БД (этап 9) |
| `services/fake-llm/` | OpenAI-совместимый mock для тестов без GPU |
| `config/`, `deploy/`, `eval/` | конфигурация, развёртывание, оценка качества |
