# vynn_core

[![License: All Rights Reserved](https://img.shields.io/badge/License-All%20Rights%20Reserved-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](.github/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-4%20passed%2C%203%20skipped-brightgreen.svg)](.github/workflows/ci.yml)

Shared article-persistence layer for MongoDB/Redis, used by the VYNN backends.
465 source lines across 12 modules.

Its one job is to make ingestion **idempotent**: the same article scraped twice
must not become two rows, and must not report itself as changed when nothing
changed.

## Install

This is a standalone repository with a `pyproject.toml`. Consumers install it by
git SHA — pin it, never track a branch, so both backends deserialise the same
document shape:

```
vynn-core @ git+https://github.com/Agentic-Analyst/vynn-core.git@a28639fc7521af7f1a6d498cfa4d343433929492
```

Both `api-runner` and `stock-analyst` currently pin `a28639f`. To work on the
library itself:

```bash
pip install -e .          # add [test] for mongomock + pytest
```

## Configure

Three environment variables. `MONGO_URI` and `MONGO_DB` have **no defaults** —
`get_db()` raises `RuntimeError` if either is unset or blank. `REDIS_URL`
defaults to `redis://localhost:6379`.

```bash
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/
MONGO_DB=your-database-name
REDIS_URL=redis://localhost:6379/0
```

These are read with `os.getenv` at import time. The package does **not** call
`load_dotenv`, so a `.env` file is not picked up automatically — load it in your
application before importing, or export the variables in the environment.

## Usage

```python
from datetime import datetime, timezone
from vynn_core import Article, init_indexes, upsert_articles, find_recent

init_indexes()  # idempotent; safe on every boot

result = upsert_articles([{
    "url": "https://example.com/nvda-earnings",
    "title": "NVIDIA Reports Q4 Earnings",
    "summary": "Record revenue driven by AI chip demand.",
    "source": "TechNews",
    "publishedAt": datetime.now(timezone.utc),
    "entities": {"tickers": ["NVDA"], "keywords": ["earnings"]},
    "quality": {"llmScore": 8.5, "reason": "High relevance"},
}])
# {"created": [...], "updated": [...], "skipped": [...]}

recent = find_recent(limit=10)
```

## Idempotency

`upsert_articles` dedupes on `urlHash` — a SHA-256 of the URL with `utm_*`
parameters stripped — which carries a unique index. Re-ingesting the same
article is a no-op, and the three-way return says which outcome each document
took:

- **created** — no row with that `urlHash` existed.
- **updated** — a row existed and at least one source field differed.
- **skipped** — a row existed and every source field matched.

A skipped document does **not** have its `updatedAt` touched. The comparison
excludes `_id`, `createdAt` and `updatedAt`, and normalises values to BSON
semantics (UTC, millisecond precision) before comparing — otherwise an aware,
microsecond-precision scraper timestamp would differ from the naive value
PyMongo returns, and every ingestion pass would report the whole corpus as
modified. `DuplicateKeyError` from a concurrent writer is caught and counted as
skipped rather than raised.

## Public API

Exported from `vynn_core/__init__.py`:

| Symbol | Signature |
| --- | --- |
| `Article` | Pydantic model; auto-fills `urlHash` from `url`; `.to_mongo_dict()` |
| `init_indexes` | `(collection_name="articles")` |
| `test_connection` | `()` → status, server version, collection names |
| `upsert_articles` | `(docs, collection_name="articles")` |
| `get_articles_by_ids` | `(ids, collection_name="articles")` |
| `find_recent` | `(collection_name="articles", limit=50, before_date=None)` |
| `get_article_by_url` | `(url, collection_name="articles")` |
| `url_hash` | `(url)` → SHA-256 of the UTM-stripped URL |
| `utc_now` | `()` → aware UTC datetime |

`collection_name` now has a default on every function that takes one, so
existing callers that already pass it positionally are unaffected. Note that
`find_recent` takes `collection_name` **first**; pass `limit` and `before_date`
as keywords.

Not exported, but importable: `vynn_core.db.mongo.get_db` /
`get_mongo_client`, `vynn_core.db.redis.get_redis_client`,
`vynn_core.feed.fanout.push`, `vynn_core.feed.ranking.compute_score`,
`vynn_core.dao.articles.get_last_n_hours_news`, and
`vynn_core.dao.users.match_user_ids_for_article` (a stub that returns `[]`;
user matching is not implemented).

## Storage

Mongo and Redis clients are lazily-created, lock-guarded singletons with
connection pooling. `init_indexes()` builds four indexes in the background:
`urlHash` (unique, the dedupe key), `publishedAt` descending,
`(publishedAt, source)` compound, and `publish_date` descending — the last
covering the ISO-string field the ingestion contract actually sorts on, so a
ticker news refresh does not sort the collection in memory.

Article documents carry `url`, `urlHash`, `title`, `summary`, `source`,
optional `image`, `publishedAt`, `entities` (`tickers`, `keywords`), `quality`
(`llmScore`, `reason`), `createdAt` and `updatedAt`.

## Tests

```bash
pip install -r requirements-test.lock
pytest -q tests
```

4 passed, 3 skipped. The 3 skips are `tests/test_mongodb.py`, an operator
connectivity script that contacts the configured database; it is skipped under
`pytest` collection so it cannot mutate a developer's real instance, and is run
directly when you want it. Unit tests use `mongomock`. CI runs this on Python
3.11 against `requirements-test.lock`.

See [INTEGRATION.md](INTEGRATION.md) for consumer-side examples.

## Licence

VYNN AI Proprietary Licence — All Rights Reserved.
Copyright (c) 2026 Zanwen Fu, VYNN AI (https://vynnai.com).
Source is available for viewing and evaluation only; see [LICENSE](LICENSE).
