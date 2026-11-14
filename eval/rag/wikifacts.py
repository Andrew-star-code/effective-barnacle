"""hit@5 поиска WeKnora на корпусе wikifacts-articles_v0 (RusBEIR), пилотный пункт 23.

Только стандартная библиотека. Данные корпуса в репозиторий не кладутся: скачиваются
с Hugging Face (kaengreg/wikifacts-articles_v0 и kaengreg/wikifacts-articles_v0-qrels).

  sample  — выборка ~200 статей и запросов, у которых все релевантные статьи в выборке
  upload  — загрузка выборки в базу знаний WeKnora и ожидание индексации
  run     — запросы к /knowledge-search, hit@5 и MRR@10 на уровне документов

Токен WeKnora — из переменной WEKNORA_TOKEN (в аргументы и логи не попадает).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

API = os.environ.get("WEKNORA_API", "http://localhost:8081/api/v1")
TIMEOUT = 300


def _request(method: str, path: str, body: bytes | None = None, ctype: str | None = None) -> Any:
    token = os.environ.get("WEKNORA_TOKEN", "")
    if not token:
        sys.exit("WEKNORA_TOKEN не задан")
    req = urllib.request.Request(API + path, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if ctype:
        req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as err:
        raise RuntimeError(f"{method} {path}: HTTP {err.code} {err.read()[:300]!r}") from err


def _json(method: str, path: str, payload: Any = None) -> Any:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    return _request(method, path, body, "application/json")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def cmd_sample(args: argparse.Namespace) -> None:
    data, out = Path(args.data), Path(args.out)
    qrels: dict[str, set[str]] = {}
    for line in (data / "dev.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        qid, cid, score = line.split("\t")
        if int(score) >= 1:
            qrels.setdefault(qid, set()).add(cid)
    queries = {str(q["_id"]): q["text"] for q in _read_jsonl(data / "queries.jsonl")}
    corpus = {str(d["_id"]): d for d in _read_jsonl(data / "corpus.jsonl")}

    rng = random.Random(args.seed)
    order = sorted(qrels)
    rng.shuffle(order)
    docs: set[str] = set()
    picked: list[str] = []
    for qid in order:
        rel = qrels[qid] & corpus.keys()
        if qid in queries and rel and len(docs | rel) <= args.docs:
            docs |= rel
            picked.append(qid)
    # Добор до нужного числа статей статьями-отвлекателями.
    rest = sorted(corpus.keys() - docs)
    rng.shuffle(rest)
    docs |= set(rest[: args.docs - len(docs)])

    (out / "docs").mkdir(parents=True, exist_ok=True)
    for cid in sorted(docs):
        d = corpus[cid]
        text = f"# {d.get('title') or 'Статья ' + cid}\n\n{d['text']}\n"
        (out / "docs" / f"wf-{cid}.md").write_text(text, encoding="utf-8")
    sample = {
        "seed": args.seed,
        "docs": sorted(docs, key=int),
        "queries": [
            {"id": q, "text": queries[q], "relevant": sorted(qrels[q], key=int)} for q in picked
        ],
    }
    (out / "sample.json").write_text(json.dumps(sample, ensure_ascii=False, indent=1), "utf-8")
    words = [len(corpus[c]["text"].split()) for c in docs]
    print(
        f"статей: {len(docs)} (в среднем {statistics.mean(words):.0f} слов), "
        f"запросов: {len(picked)}"
    )


def _upload(kb: str, path: Path) -> str:
    boundary = uuid.uuid4().hex
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        "Content-Type: text/markdown\r\n\r\n"
    ).encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    resp = _request(
        "POST", f"/knowledge-bases/{kb}/knowledge/file", body,
        f"multipart/form-data; boundary={boundary}",
    )
    return str(resp["data"]["id"])


def cmd_upload(args: argparse.Namespace) -> None:
    out = Path(args.out)
    state_path = out / "uploaded.json"
    state: dict[str, str] = json.loads(state_path.read_text("utf-8")) if state_path.exists() else {}
    for path in sorted((out / "docs").glob("wf-*.md")):
        if path.stem in state.values():
            continue
        state[_upload(args.kb, path)] = path.stem
        state_path.write_text(json.dumps(state, indent=1), "utf-8")
    print(f"загружено: {len(state)}; жду индексации")
    started = time.monotonic()
    pending = set(state)
    while pending:
        for kid in list(pending):
            st = _json("GET", f"/knowledge/{kid}")["data"].get("parse_status")
            if st in ("completed", "failed"):
                pending.discard(kid)
                if st == "failed":
                    print(f"ошибка индексации: {state[kid]}")
        print(f"  осталось {len(pending)} ({time.monotonic() - started:.0f} с)", flush=True)
        if pending:
            time.sleep(20)


MODES: dict[str, dict[str, Any]] = {
    "bm25": {"disable_vector_match": True, "rerank": {"enabled": False}},
    "vector": {"disable_keywords_match": True, "rerank": {"enabled": False}},
    "hybrid": {"rerank": {"enabled": False}},
    # Порог не режет кандидатов: меряется порядок, а не отсечение.
    "hybrid_rerank": {"rerank": {"enabled": True, "top_k": 20, "threshold": -1000.0}},
}


def cmd_run(args: argparse.Namespace) -> None:
    out = Path(args.out)
    sample = json.loads((out / "sample.json").read_text("utf-8"))
    kid_to_doc = {k: v.removeprefix("wf-") for k, v in
                  json.loads((out / "uploaded.json").read_text("utf-8")).items()}
    queries = sample["queries"][: args.limit] if args.limit else sample["queries"]
    rows, hits5, rr, lat = [], 0, 0.0, []
    for q in queries:
        payload = {"query": q["text"], "knowledge_base_id": args.kb, "match_count": 20,
                   **MODES[args.mode]}
        t0 = time.monotonic()
        res = _json("POST", "/knowledge-search", payload)["data"] or []
        lat.append(time.monotonic() - t0)
        ranked: list[str] = []
        for r in res:
            doc = kid_to_doc.get(r.get("knowledge_id", ""))
            if doc and doc not in ranked:
                ranked.append(doc)
        rel = set(q["relevant"])
        first = next((i for i, d in enumerate(ranked[:10]) if d in rel), None)
        hits5 += first is not None and first < 5
        rr += 0.0 if first is None else 1.0 / (first + 1)
        rows.append({"id": q["id"], "top": ranked[:10], "relevant": q["relevant"], "rank": first})
    n = len(queries)
    summary = {
        "label": args.label, "mode": args.mode, "queries": n,
        "hit@5": round(hits5 / n, 4), "mrr@10": round(rr / n, 4),
        "latency_p50_s": round(statistics.median(lat), 2),
        "latency_max_s": round(max(lat), 2),
    }
    (out / f"result-{args.label}-{args.mode}.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=1), "utf-8")
    print(json.dumps(summary, ensure_ascii=False))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--data", required=True, help="каталог с corpus.jsonl, queries.jsonl, dev.tsv")
    s.add_argument("--out", required=True)
    s.add_argument("--docs", type=int, default=200)
    s.add_argument("--seed", type=int, default=42)
    u = sub.add_parser("upload")
    u.add_argument("--out", required=True)
    u.add_argument("--kb", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", required=True)
    r.add_argument("--kb", required=True)
    r.add_argument("--mode", choices=sorted(MODES), required=True)
    r.add_argument("--label", required=True, help="например, before-p01 / after-p01")
    r.add_argument("--limit", type=int, default=0)
    args = p.parse_args()
    {"sample": cmd_sample, "upload": cmd_upload, "run": cmd_run}[args.cmd](args)


if __name__ == "__main__":
    main()
