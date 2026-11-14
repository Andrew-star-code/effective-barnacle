# Оценка поиска (RAG)

hit@5 и MRR@10 поиска WeKnora на уровне документов (SPEC §11.6, пилотный пункт 23).

## wikifacts — открытый русский корпус

[`wikifacts.py`](wikifacts.py) меряет поиск на корпусе `wikifacts-articles_v0` из бенчмарка RusBEIR:
полные статьи русской Википедии (~2 500 слов) и запросы-факты с разметкой «запрос → статья»
(оценки 1–2 считаются релевантными). Свои документы заказчика с разметкой появятся позже —
тогда тот же скрипт или его аналог прогоняется на них.

Корпус в git не кладётся (81 МБ, лицензия на карточке датасета — MIT, источник — Википедия):

```bash
mkdir -p /tmp/wikifacts && cd /tmp/wikifacts
curl -sSLO https://huggingface.co/datasets/kaengreg/wikifacts-articles_v0/resolve/main/corpus.jsonl
curl -sSLO https://huggingface.co/datasets/kaengreg/wikifacts-articles_v0/resolve/main/queries.jsonl
curl -sSLO https://huggingface.co/datasets/kaengreg/wikifacts-articles_v0-qrels/resolve/main/dev.tsv
```

Прогон (WeKnora с настоящими эмбеддингами — профиль `WEKNORA_MODELS_FILE=builtin_models.ollama.yaml`;
на fake-llm описания документов одинаковые и портят векторный поиск):

```bash
python3 eval/rag/wikifacts.py sample --data /tmp/wikifacts --out /tmp/wf-run   # 200 статей, seed 42
# создать базу знаний в WeKnora; WEKNORA_TOKEN — JWT пользователя
python3 eval/rag/wikifacts.py upload --out /tmp/wf-run --kb <id базы>
python3 eval/rag/wikifacts.py run --out /tmp/wf-run --kb <id базы> --mode hybrid_rerank --label before-p01
```

Режимы `--mode`: `bm25`, `vector`, `hybrid`, `hybrid_rerank` (через `/knowledge-search`, 20 кандидатов;
у реранка порог не режет кандидатов — меряется порядок). Результат — `result-<label>-<mode>.json`
в каталоге `--out`. Результаты прогонов — в `docs/status.md`.
