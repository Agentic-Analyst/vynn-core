import mongomock
import pytest
from vynn_core.dao.articles import upsert_articles, get_articles_by_ids
from vynn_core.db.mongo import get_db, init_indexes
from vynn_core.utils.time import utc_now
from unittest import mock

@mock.patch("vynn_core.db.mongo.get_mongo_client", new=lambda: mongomock.MongoClient())
def test_upsert_articles():
    init_indexes()
    article = {
        "url": "https://example.com/a",
        "title": "Example",
        "summary": "...",
        "source": "Example",
        "publishedAt": utc_now(),
        "entities": {"tickers": ["AAPL"], "keywords": ["earnings"]},
        "quality": {"llmScore": 0.82, "reason": "Keyword & recency"}
    }
    res = upsert_articles([article])
    assert len(res["created"]) == 1
    ids = res["created"] + res["updated"]
    fetched = get_articles_by_ids(ids)
    assert fetched[0]["title"] == "Example"
