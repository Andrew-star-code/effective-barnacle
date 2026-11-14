# Команды проекта (SPEC §5, §19.2). Нужны: bash, make, uv, node + pnpm, docker.
# На Windows запускать из WSL2 (см. README.md).
SHELL := bash
.DEFAULT_GOAL := help

CORP_EXT := services/corp-ext
FAKE_LLM := services/fake-llm
ADMIN    := services/corp-admin
PY_SERVICES := $(CORP_EXT) $(FAKE_LLM)
PNPM ?= pnpm
COMPOSE := docker compose -f deploy/compose/compose.dev.yml

.PHONY: help install hooks lint test build images gen-api gen-api-check docs-check check \
        migrate dev-up dev-down dev-logs e2e deploy weknora-build lang-scan

help: ## список команд
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

install: hooks ## зависимости по lock-файлам и git-хуки
	@for s in $(PY_SERVICES); do (cd $$s && uv sync --frozen) || exit 1; done
	cd $(ADMIN) && $(PNPM) install --frozen-lockfile

hooks: ## включить git-хуки из tools/hooks
	git config core.hooksPath tools/hooks

lint: ## ruff, mypy, vue-tsc
	@for s in $(PY_SERVICES); do \
	  echo "== lint $$s"; \
	  (cd $$s && uv run ruff check . && uv run ruff format --check . && uv run mypy) || exit 1; \
	done
	cd $(ADMIN) && $(PNPM) typecheck

test: ## unit-тесты
	@for s in $(PY_SERVICES); do echo "== test $$s"; (cd $$s && uv run pytest -q) || exit 1; done
	cd $(ADMIN) && $(PNPM) test

build: ## сборка фронтенда corp-admin
	cd $(ADMIN) && $(PNPM) build

images: ## сборка своих образов (нужен запущенный Docker)
	$(COMPOSE) build

gen-api: ## OpenAPI corp-ext → типы клиента corp-admin
	cd $(CORP_EXT) && uv run python -m app.cli openapi > ../corp-admin/openapi.json
	cd $(ADMIN) && $(PNPM) gen-api

gen-api-check: ## сгенерированный клиент совпадает с OpenAPI corp-ext
	@cd $(CORP_EXT) && uv run python -m app.cli openapi | diff -q - ../corp-admin/openapi.json >/dev/null \
	  || { echo "openapi.json устарел: выполните make gen-api"; exit 1; }

docs-check: gen-api-check ## README модулей, ссылки в документации, реестр патчей
	python3 tools/docs_check.py

# SKIP_IMAGES=1 make check — без сборки образов (например, когда Docker не запущен)
check: lint test build docs-check $(if $(SKIP_IMAGES),,images) ## всё перед пушем
	@echo "make check: OK"

migrate: ## миграции схемы corp (нужен доступный Postgres)
	cd $(CORP_EXT) && uv run alembic upgrade head

dev-up: ## поднять dev-стек
	$(COMPOSE) up -d --build --wait

dev-down: ## остановить dev-стек
	$(COMPOSE) down

dev-logs: ## логи dev-стека
	$(COMPOSE) logs -f --tail=100

e2e: ## e2e-тесты Playwright — этап 1
	@echo "e2e: не реализовано (этап 1, SPEC §20.1)"; exit 1

weknora-build: ## образы WeKnora из подмодуля — этап 0, после решения по форку
	@echo "weknora-build: не реализовано (этап 0, docs/status.md)"; exit 1

lang-scan: ## поиск иероглифов в пользовательских строках WeKnora — этап 2
	@echo "lang-scan: не реализовано (этап 2, SPEC §13.4)"; exit 1

deploy: ## выкатка на сервер — этап 10
	@echo "deploy: не реализовано (этап 10, SPEC §18.2)"; exit 1
