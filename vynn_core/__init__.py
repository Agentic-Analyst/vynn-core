"""
vynn_core - Minimal, production-ready news feed data layer for MongoDB/Redis.

This package provides core functionality for:
- Article storage and retrieval in MongoDB
- URL deduplication using hashing
- Basic feed operations with Redis
- Pydantic models for data validation
"""

__version__ = "0.1.0"

# Import core functionality for easy access
from .models import Article
from .db.mongo import init_indexes, test_connection
from .dao.articles import upsert_articles, get_articles_by_ids, find_recent, get_article_by_url
from .utils.hashing import url_hash
from .utils.time import utc_now

__all__ = [
    "Article",
    "init_indexes", 
    "test_connection",
    "upsert_articles",
    "get_articles_by_ids", 
    "find_recent",
    "get_article_by_url",
    "url_hash",
    "utc_now"
]
