# AGENTS.md — правила и карта проекта

Для людей и ИИ-агентов. Требования — в [docs/SPEC.md](docs/SPEC.md), прогресс и открытые вопросы — в [docs/status.md](docs/status.md).

## 1. Что за проект

- Корпоративный ИИ-ассистент в закрытом контуре: веб-чат с RAG для 200+ сотрудников и API моделей для разработчиков.
- Основа — открытый проект WeKnora (Go + Vue 3), подключён подмодулем `weknora/`; его код меняется только патчами из реестра.
- Свой код рядом: `corp-ext` (Python, FastAPI), `corp-admin` (Vue 3 + TDesign), `data-gateway` (Python, MCP), `fake-llm` (mock для тестов).
- Вход — Keycloak с федерацией AD; права на базы знаний — через пространства и организации WeKnora.
- Всё работает на одном GPU-сервере без обращений в интернет.

## 2. Команды

| Команда | Что делает |
| --- | --- |
| `make install` | зависимости по lock-файлам, git-хуки |
| `make dev-up` / `make dev-down` | dev-стек в Docker Compose |
| `make check` | всё перед пушем: `lint`, `test`, `build`, `docs-check`, сборка образов (`SKIP_IMAGES=1` — без неё) |
| `make test` | unit-тесты (pytest, Vitest) |
| `make lint` | ruff, mypy, vue-tsc |
| `make gen-api` | OpenAPI `corp-ext` → типы клиента `corp-admin` |
| `make migrate` | миграции схемы `corp` |
| `make docs-check` | README модулей, ссылки, реестр патчей, актуальность API-клиента |
| `make e2e`, `make weknora-build`, `make lang-scan`, `make deploy` | заглушки до соответствующих этапов |

Нужны `bash`, `make`, `uv`, Node 22 + `pnpm`, Docker. На Windows — из WSL2.

## 3. Карта репозитория

```text
docs/        SPEC.md, status.md, patches.md, adr/, architecture/, guides/, reference/, runbooks/
weknora/     подмодуль: форк WeKnora (SPEC §2.4)
services/
  corp-ext/      app/core, app/modules/<модуль>/ (у каждого README), app/workers, app/cli, migrations/, tests/
  corp-admin/    src/pages, src/router, src/layouts, src/i18n, src/api (генерируется), tests/
  data-gateway/  семантический слой SQL + catalog/*.yaml
  fake-llm/      OpenAI-совместимый mock со сценариями
config/      weknora/, keycloak/, scenarios/, moderation/, limits/, templates/, corp-ext.example.yaml
deploy/      compose/, nginx/, models/, monitoring/, mock-ad/, offline/
eval/        rag/, scenarios/, language/
tools/       docs_check.py, hooks/
```

### Карта изменений

| Хочу… | Где править | Что обновить вместе с этим |
| --- | --- | --- |
| Изменить вид сообщения, кнопки под ним | `weknora/frontend/src/views/chat/` — это патч | `docs/patches.md`, e2e-тест |
| Добавить корпоративный инструмент для модели | `services/corp-ext/app/modules/mcp/` или `services/data-gateway/` | `docs/guides/add-mcp-tool.md`, тест на fake-LLM |
| Добавить сценарий | админка WeKnora (агент) + `config/scenarios/*.yaml` для seed | промпт сценария, расшаривание в организации (SPEC §9.3) |
| Сменить или добавить модель | `config/weknora/builtin_models.yaml` + `deploy/models/` | `docs/runbooks/models.md` |
| Изменить системный промпт | промпт агента в админке WeKnora или `config/weknora/prompt_templates/` | прогон `eval/scenarios` и `eval/language` |
| Добавить поле профиля из AD | маппер в Keycloak/`adsync` + `modules/profile/` + миграция `corp` | `docs/guides/ad-setup.md`; если поле нужно в промпте — P-02 |
| Добавить страницу админки | `services/corp-admin/src/pages/` + `corp-ext/app/modules/<модуль>/` | новое право в `docs/reference/permissions.md` |
| Добавить метрику лимитов | `services/corp-ext/app/modules/limits/` | `config/limits/policies.yaml`, `docs/reference/config.md` |
| Добавить тип инцидента | `services/corp-ext/app/modules/incidents/` | фильтры в `corp-admin` |
| Добавить набор данных или функцию SQL | `services/data-gateway/catalog/` | описания полей и примеры запросов |
| Поменять правила раскладки по пространствам | `services/corp-ext/app/modules/provisioning/` | `docs/architecture/access-model.md`, тесты изоляции |
| Добавить источник членства в группах | `services/corp-ext/app/modules/groups/sources/` | `docs/guides/add-group-source.md`, тест пробного прогона |
| Изменить код WeKnora | только по `docs/guides/write-weknora-patch.md` | `docs/patches.md`, тест патча |
| Изменить схему `corp` | модель SQLAlchemy + миграция Alembic | `docs/reference/db-schema-corp.md` (генерируется) |

## 4. Соглашения

- Язык: идентификаторы и сообщения коммитов — на английском; документация и комментарии — на русском.
- Коммиты — Conventional Commits (`feat(corp-ext): …`); коммиты патчей в форке WeKnora — с префиксом `P-NN:`.
- Python 3.12: `ruff` (линт и формат), `mypy --strict`, зависимости через `uv`, версии закреплены `uv.lock`.
- Фронтенд: TypeScript strict, `pnpm`, все строки интерфейса — через i18n, русский по умолчанию.
- Новая зависимость — только с обоснованием в ADR или описании изменения.
- Секреты — только из файлов секретов или переменных окружения; в git, YAML и логи не попадают.
- Новые промпты — на русском или английском, с `{{language}}`, без китайских примеров.

### Как писать код: главное

Подробно и с причинами — [docs/guides/coding.md](docs/guides/coding.md); прочитать перед первой задачей с кодом.

1. Факты о WeKnora проверять по коду в `weknora/` на закреплённом теге (`git -C weknora grep`), а не по памяти и не по SPEC. Расхождение кода со SPEC — находка для `docs/status.md`, а не повод подгонять.
2. API библиотек брать из установленных пакетов: версии в lock-файлах новее знаний модели.
3. Писать только то, что нужно текущему этапу; без заготовок и абстракций на будущее.
4. Модуль `corp-ext`: `router.py` (тонкий) → `service.py` (логика, без FastAPI) → `models.py`, `schemas.py`, `tasks.py`. Новый `models.py` — зарегистрировать в `app/core/model_registry.py`.
5. Пользователь — только из проверенного JWT или подписанного `X-Corp-User`, никогда из тела запроса и аргументов модели. Права и владение проверяет сервер; действие админа над чужими данными пишет аудит в той же транзакции.
6. SQL — только с параметрами. Конфиг — только через `Settings`. Время — UTC с часовым поясом. Внешние вызовы — с тайм-аутом. В async-коде нет блокирующих вызовов.
7. Синхронизация и `provision` идемпотентны и имеют `--dry-run`.
8. Поменял маршрут или схему API — `make gen-api`, сгенерированные файлы в тот же коммит.
9. Тесты безопасности из SPEC §20.2 — часть задачи, вводящей функцию. Проверки нельзя ослаблять, чтобы стало зелёным; `# noqa` и `# type: ignore` — только с кодом и причиной.
10. Заглушка падает громко и называет этап, а не молча возвращает успех.
11. В отчёте и в `docs/status.md` разделять «проверено запуском», «проверено статически» и «не проверено».

## 5. Порядок работы

- Задачу берёт либо человек, либо агент; кто чем занят — в `docs/status.md`.
- Каждая задача — в своей ветке: `agent/<задача>` или `<имя>/<задача>`.
- В `main` и в ветку `corp/v<версия>` форка изменения вливает человек после просмотра диффа и зелёного `make check`.
- `make check` обязателен перед каждым пушем; быстрые проверки при коммите — git-хуки (`make hooks`).
- Агент работает этапами (SPEC §21–22): перед этапом читает §22, §2.4, сам этап и связанные разделы; план этапа и демо-сценарий записывает в `docs/status.md`.
- Неясное не додумывать: вопрос — в `docs/status.md`, вариант по умолчанию — из SPEC, в коде — `TODO(question)`.

## 6. Definition of Done

Код; тесты (unit, а для пользовательского потока — интеграционный или e2e); миграции; перегенерированный API-клиент (`make gen-api`); обновлённые README модуля, SPEC, guides и реестр патчей, если поменялось поведение; запись в `docs/status.md` и `CHANGELOG.md`.

## 7. Подводные камни

- Язык генераций WeKnora задаётся `WEKNORA_LANGUAGE=ru-RU`; без него — китайский.
- Код WeKnora меняется только через реестр патчей (`docs/patches.md`); порядок выбора: конфигурация и API → MCP или nginx → свой сервис → патч.
- `corp-ext` не пишет в таблицы WeKnora (четыре исключения — SPEC §16.2) и читает их только через `app/modules/weknora/`.
- Права на базы знаний — через пространства и организации, а не через фильтры поиска.
- Системный промпт агента не секрет: сотрудник может его прочитать и создать своего агента. Контроль — guard-модель, а не промпт (ADR 0013).
- Миграции в форк WeKnora не добавляются: нумерация сквозная, конфликт с апстримом (ADR 0014).
- Чат-эндпоинты идут через прокси `corp-ext`: поток ответа нельзя буферизовать ни там, ни в nginx.
- SSE за nginx — без буферизации (`proxy_buffering off`).
- `JWT_SECRET` WeKnora задаётся явно, иначе сессии слетают при перезапуске.
- Секреты не логируются и не кладутся в переменные навыков песочницы; на уровне INFO не логируются тексты сообщений.
- Никаких внешних сетевых вызовов в рантайме и никаких CDN.
- Логи `corp-ext` идут в stdout: команды CLI, печатающие данные в stdout (например, `openapi`), должны их приглушать.
