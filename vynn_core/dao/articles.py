from ..db.mongo import get_db
from ..models import Article
from ..utils.time import utc_now
from ..utils.hashing import url_hash
from pymongo.errors import DuplicateKeyError
from typing import List, Dict, Union
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

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
            
            # Ensure urlHash is present
            if not doc_dict.get("urlHash"):
                doc_dict["urlHash"] = url_hash(doc_dict["url"])
            
            # Set timestamps
            now = utc_now()
            doc_dict.setdefault("createdAt", now)
            doc_dict["updatedAt"] = now
            
            # Upsert operation
            result = collection.update_one(
                {"urlHash": doc_dict["urlHash"]},
                {
                    "$set": {k: v for k, v in doc_dict.items() if k != "createdAt"},
                    "$setOnInsert": {"createdAt": doc_dict["createdAt"]}
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

def find_recent(limit: int = 50, source: str = None, collection_name: str = "articles") -> List[dict]:
    """Find recent articles, optionally filtered by source."""
    db = get_db()
    collection = db[collection_name]
    try:
        query = {}
        if source:
            query["source"] = source
        return list(collection.find(query).sort("publishedAt", -1).limit(limit))
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
