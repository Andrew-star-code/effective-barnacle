-- P-01: русский BM25-индекс для таблицы embeddings WeKnora (SPEC §11.2, ADR 0014).
-- Штатный индекс (migrations/versioned/000002_embeddings.up.sql) собран с chinese_lindera через
-- legacy-параметр text_fields: без стемминга, без стоп-слов и без приведения к нижнему регистру.
-- Этот SQL войдёт в идемпотентный шаг `provision --search-index` (этап 3); на пилоте выполняется
-- вручную: psql -v ON_ERROR_STOP=1 -f search_index.sql
--
-- Требования (проверено на ParadeDB pg_search 0.25.11, 14.11.2026):
-- * запросы WeKnora (`content ||| :query`) разбираются токенизатором индекса — сами на
--   chinese_lindera не завязаны (internal/application/repository/retriever/postgres/repository.go);
-- * имя индекса прежнее — embeddings_search_idx: на него ссылаются миграции WeKnora (REINDEX).
-- Пересоздание блокирует запись в embeddings на время построения: выполнять в окно выкатки.

BEGIN;

DROP INDEX IF EXISTS embeddings_search_idx;

CREATE INDEX embeddings_search_idx ON embeddings
USING bm25 (
    id,
    (knowledge_base_id::pdb.literal),
    (content::pdb.simple('stemmer=russian', 'stopwords_language=russian')),
    (knowledge_id::pdb.literal),
    (chunk_id::pdb.literal)
)
WITH (key_field = 'id');

COMMIT;
