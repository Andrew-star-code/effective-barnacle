# Документация

| Документ | Содержание |
| --- | --- |
| [SPEC.md](SPEC.md) | требования и план этапов — единственный источник требований |
| [status.md](status.md) | прогресс этапов, вопросы к плану, пункты пилота, демо-сценарии |
| [patches.md](patches.md) | реестр патчей WeKnora |
| [adr/](adr/README.md) | архитектурные решения |
| [architecture/](architecture/README.md) | обзор, поток запроса, модель доступа, модель данных, безопасность |
| [guides/](guides/README.md) | пошаговые инструкции «как добавить…» |
| [reference/](reference/README.md) | конфиг, API `corp-ext`, права, схема `corp` — генерируются |
| [runbooks/](runbooks/README.md) | эксплуатация: модели, бэкапы, инциденты, секреты, обновление WeKnora |

Как устроена сама WeKnora — в её документации: `weknora/website-docs/`.

Документация — часть Definition of Done (SPEC §19). `make docs-check` проверяет README модулей, ссылки и реестр патчей.
