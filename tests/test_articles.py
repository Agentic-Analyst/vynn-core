import mongomock
import pytest
from vynn_core.dao.articles import upsert_articles, get_articles_by_ids
from vynn_core.db.mongo import get_db, init_indexes
from vynn_core.utils.time import utc_now
from unittest import mock

def test_upsert_articles(monkeypatch):
    client = mongomock.MongoClient()
    monkeypatch.setattr("vynn_core.db.mongo.get_mongo_client", lambda: client)
    monkeypatch.setattr("vynn_core.db.mongo.MONGO_DB", "vynn_core_test")
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
    first_updated_at = fetched[0]["updatedAt"]

    duplicate = upsert_articles([article])
    assert duplicate["created"] == []
    assert duplicate["updated"] == []
    assert len(duplicate["skipped"]) == 1
    assert get_articles_by_ids(ids)[0]["updatedAt"] == first_updated_at

    changed = {**article, "summary": "Updated summary"}
    update = upsert_articles([changed])
    assert len(update["updated"]) == 1
    assert get_articles_by_ids(update["updated"])[0]["summary"] == "Updated summary"
