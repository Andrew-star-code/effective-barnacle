# Конфигурация WeKnora

Переменные окружения, каталог моделей, системные настройки и переопределения промптов (SPEC §18.4).

Статус: заготовка, наполнение — этап 2.

Планируемый состав:

- `.env.weknora.example` — есть; рабочий .env.weknora в git не попадает
- `builtin_models.dev.yaml` — есть: каталог моделей dev-стека, все модели — fake-llm (по умолчанию)
- `builtin_models.ollama.yaml` — есть: `qwen3.5:9b` и `bge-m3` через Ollama на машине разработчика;
  включается `WEKNORA_MODELS_FILE=builtin_models.ollama.yaml make dev-up`;
  в обоих профилях реранкер — `BAAI/bge-reranker-v2-m3` в сервисе `rerank` (TEI на CPU)
- `builtin_models.yaml` — прод-каталог
- `system_settings.yaml`
- `prompt_templates/`
