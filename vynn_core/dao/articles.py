from ..db.mongo import get_db
from ..models import Article
from ..utils.time import utc_now
from ..utils.hashing import url_hash
from pymongo.errors import DuplicateKeyError
from typing import List, Dict, Union
from bson import ObjectId
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


def _mongo_normalize(value):
    """Mirror BSON datetime semantics before comparing or persisting values.

    MongoDB stores datetimes as UTC milliseconds and PyMongo returns them as
    naive UTC by default.  Comparing an aware, microsecond-precision scraper
    timestamp with the stored value otherwise makes an unchanged article look
    modified on every ingestion pass.
    """
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value.replace(microsecond=(value.microsecond // 1000) * 1000)
    if isinstance(value, dict):
        return {key: _mongo_normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_mongo_normalize(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_mongo_normalize(item) for item in value)
    return value

def upsert_articles(docs: List[Union[dict, Article]], collection_name: str = "articles") -> Dict[str, List[str]]:
    """
    Upsert articles to MongoDB. Returns counts of created, updated, and skipped articles.
    
    Args:
        docs: List of article dictionaries or Article models
        collection_name: Name of the MongoDB collection to save to (default: "articles")
        
    Returns:
        Dict with keys: created, updated, skipped (each containing list of ObjectId strings)
    """
    db = get_db()
    collection = db[collection_name]
    created, updated, skipped = [], [], []
    
    for doc in docs:
        try:
            # Convert Article model to dict if needed
            if isinstance(doc, Article):
                doc_dict = doc.to_mongo_dict()
            else:
                doc_dict = doc.copy()

            doc_dict = _mongo_normalize(doc_dict)
            
            # Ensure urlHash is present
            if not doc_dict.get("urlHash"):
                doc_dict["urlHash"] = url_hash(doc_dict["url"])
            
            # Updating ``updatedAt`` before comparing made every identical
            # article look modified, so the advertised ``skipped`` outcome was
            # unreachable.  Compare source fields first and touch updatedAt
            # only when content actually changed.
            existing = collection.find_one({"urlHash": doc_dict["urlHash"]})
            comparable = {
                key: value for key, value in doc_dict.items()
                if key not in {"_id", "createdAt", "updatedAt"}
            }
            if existing is not None and all(
                _mongo_normalize(existing.get(key)) == value
                for key, value in comparable.items()
            ):
                skipped.append(doc_dict["urlHash"])
                logger.debug(
                    f"Skipped article (no changes): {doc_dict.get('title', 'Unknown')}"
                )
                continue

            now = utc_now()
            update_fields = {**comparable, "updatedAt": now}
            
            # Upsert operation
            result = collection.update_one(
                {"urlHash": doc_dict["urlHash"]},
                {
                    "$set": update_fields,
                    "$setOnInsert": {"createdAt": doc_dict.get("createdAt") or now}
                },
                upsert=True
            )
            
            if result.upserted_id:
                created.append(str(result.upserted_id))
                logger.info(f"Created article: {doc_dict.get('title', 'Unknown')}")
            elif result.modified_count > 0:
                # Find the updated document
                existing = collection.find_one({"urlHash": doc_dict["urlHash"]})
                if existing:
                    updated.append(str(existing["_id"]))
                    logger.info(f"Updated article: {doc_dict.get('title', 'Unknown')}")
            else:
                skipped.append(doc_dict["urlHash"])
                logger.debug(f"Skipped article (no changes): {doc_dict.get('title', 'Unknown')}")
                
        except DuplicateKeyError:
            skipped.append(doc_dict.get("urlHash", "unknown"))
            logger.warning(f"Duplicate key error for article: {doc_dict.get('title', 'Unknown')}")
        except Exception as e:
            skipped.append(doc_dict.get("urlHash", "unknown"))
            logger.error(f"Error upserting article {doc_dict.get('title', 'Unknown')}: {e}")
    
    return {"created": created, "updated": updated, "skipped": skipped}

def get_articles_by_ids(ids: List[str], collection_name: str = "articles") -> List[dict]:
    """Get articles by their MongoDB ObjectId strings."""
    db = get_db()
    collection = db[collection_name]
    try:
        object_ids = [ObjectId(id_str) for id_str in ids if ObjectId.is_valid(id_str)]
        return list(collection.find({"_id": {"$in": object_ids}}))
    except Exception as e:
        logger.error(f"Error fetching articles by IDs: {e}")
        return []

def find_recent(collection_name: str = "articles", limit: int = 50, before_date: str = None) -> List[dict]:
    """
    Find recent articles, optionally filtered by date and source.
    
    Args:
        limit: Maximum number of articles to return (default: 50)
        before_date: ISO format timestamp string (e.g., "2025-10-29T18:06:29.275930"). 
                     Returns only articles published before this date.
        source: Filter by article source (optional)
        collection_name: Name of the MongoDB collection (default: "articles")
        
    Returns:
        List of article documents sorted by publish_date in descending order
    """
    db = get_db()
    collection = db[collection_name]
    try:
        query = {}
        
        # Filter by date if provided
        if before_date:
            query["publish_date"] = {"$lt": before_date}
            
        return list(collection.find(query).sort("publish_date", -1).limit(limit))
    except Exception as e:
        logger.error(f"Error fetching recent articles: {e}")
        return []

def get_article_by_url(url: str, collection_name: str = "articles") -> dict:
    """Get article by URL (using urlHash for efficient lookup)."""
    db = get_db()
    collection = db[collection_name]
    try:
        url_hash_value = url_hash(url)
        return collection.find_one({"urlHash": url_hash_value})
    except Exception as e:
        logger.error(f"Error fetching article by URL: {e}")
        return None

def get_last_n_hours_news(collection_name: str = "articles", n_hours_ago: int = 24) -> List[dict]:
    """
    Get articles from the last n hours.

    Uses real-time UTC to calculate the cutoff time, ensuring it works correctly
    in Docker containers and across different timezones.
    
    Args:
        collection_name: Name of the MongoDB collection
        n_hours: Number of hours to look back
        
    Returns:
        List of article documents from the last n hours, sorted by publish_date descending
    """
    from datetime import timedelta
    
    db = get_db()
    collection = db[collection_name]
    try:
        # Get current UTC time and calculate cutoff
        now = utc_now()
        cutoff_datetime = now - timedelta(hours=n_hours_ago)
        
        # Format as ISO string without timezone suffix to match DB format
        # Database stores: "2025-11-01T15:56:39.542998"
        cutoff_time = cutoff_datetime.replace(tzinfo=None).isoformat()

        # Query for articles published after the cutoff time
        query = {"publish_date": {"$gte": cutoff_time}}

        logger.info(f"Fetching articles from last {n_hours_ago} hours (cutoff: {cutoff_time}, current UTC: {now.replace(tzinfo=None).isoformat()})")
        results = list(collection.find(query).sort("publish_date", -1))
        logger.info(f"Found {len(results)} articles from last {n_hours_ago} hours")

        return results
    except Exception as e:
        logger.error(f"Error fetching last {n_hours_ago} hours news: {e}")
        return []
