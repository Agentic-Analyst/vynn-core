# vynn-core

The shared news data layer behind [VYNN AI](https://vynnai.com): articles stored once in MongoDB and deduplicated by URL, and per-user feeds in Redis. The [agent](https://github.com/Agentic-Analyst/stock-analyst) and VYNN's API both depend on it, pinned to a commit.

## Install

```bash
pip install "vynn-core @ git+https://github.com/Agentic-Analyst/vynn-core.git"
```

Requires Python 3.9 or later. In production, pin a commit (`...vynn-core.git@<commit>`), as the agent does.

## Configure

vynn-core reads its settings from the environment when it is imported. It does not load a `.env` file itself, so load yours first (for example with `python-dotenv`).

| Variable | Default | Purpose |
|---|---|---|
| `MONGO_URI` | none, required | Article storage |
| `MONGO_DB` | none, required | The database to use |
| `REDIS_URL` | `redis://localhost:6379` | Feed fan-out |

## Use

```python
from datetime import datetime, timezone

from vynn_core import find_recent, init_indexes, upsert_articles

init_indexes()  # idempotent: safe to call on every start

result = upsert_articles([{
    "url": "https://example.com/nvda-earnings?utm_source=newsletter",
    "title": "NVIDIA reports record revenue",
    "summary": "Data center demand drove the quarter.",
    "source": "Example News",
    "publishedAt": datetime.now(timezone.utc),
    "entities": {"tickers": ["NVDA"], "keywords": ["earnings"]},
}])
print(result)  # {"created": [...], "updated": [...], "skipped": [...]}

for article in find_recent(limit=5):
    print(article["title"], "|", article["source"])
```

Saving the same article again, even with different `utm_*` tracking parameters, never creates a second record: an unchanged copy is skipped and a changed one updates it.

## API

| Function | What it does |
|---|---|
| `init_indexes()` | Creates the indexes below; idempotent |
| `test_connection()` | Checks that MongoDB is reachable |
| `upsert_articles(docs)` | Saves dicts or `Article` models, deduplicated by URL; returns created and updated IDs and the URL hashes it skipped |
| `get_articles_by_ids(ids)` | Fetches articles by ID |
| `get_article_by_url(url)` | Fetches one article by its URL |
| `find_recent(limit=50, before_date=None)` | The newest articles first |
| `url_hash(url)` | SHA-256 of the URL with `utm_*` parameters removed |
| `utc_now()` | The current time in UTC |
| `Article` | The Pydantic model; fills in `urlHash` from the URL |

For feeds, `vynn_core.dao.users.match_user_ids_for_article(entities)` finds users whose watchlist holds an article's tickers, `vynn_core.feed.ranking.compute_score(...)` scores it for a user, and `vynn_core.feed.fanout.push(article_id, user_ids, score)` adds it to each user's Redis feed (`feed:<user_id>`).

## Data model

An article in the `articles` collection:

| Field | Type |
|---|---|
| `url`, `urlHash` | The source URL, and its hash (unique) |
| `title`, `summary`, `source` | Text |
| `image` | Optional URL |
| `publishedAt` | When the source published it |
| `entities` | `{"tickers": [...], "keywords": [...]}` |
| `quality` | `{"llmScore": ..., "reason": ...}`, from the agent's screening |
| `createdAt`, `updatedAt` | Set on write |

Indexes: `urlHash` (unique), `publishedAt` with `source`, `publishedAt`, and `publish_date` (the timestamp field the agent's news ingestion writes), plus `watchlist.tickers` on `users` for feed matching.

## Tests

```bash
pip install -e ".[test]"
python -m pytest tests/ -q
```

The MongoDB tests are skipped unless `MONGO_URI` points at a database; the others need no services.

More examples: [INTEGRATION.md](INTEGRATION.md).

## License

Source-available, all rights reserved; see [LICENSE](LICENSE).
