from pymongo import MongoClient, ASCENDING, DESCENDING
from ..config import MONGO_URI, MONGO_DB
from threading import Lock
import logging

logger = logging.getLogger(__name__)

_mongo_client = None
_mongo_lock = Lock()

def get_mongo_client():
    """Get singleton MongoDB client with connection pooling."""
    global _mongo_client
    if not isinstance(MONGO_URI, str) or not MONGO_URI.strip():
        raise RuntimeError("MONGO_URI is not configured")
    if _mongo_client is None:
        with _mongo_lock:
            if _mongo_client is None:
                try:
                    _mongo_client = MongoClient(MONGO_URI)
                    # Test connection
                    _mongo_client.admin.command('ping')
                    logger.info("MongoDB connection established successfully")
                except Exception as e:
                    logger.error(f"Failed to connect to MongoDB: {e}")
                    raise
    return _mongo_client

def get_db():
    """Get the configured database."""
    if not isinstance(MONGO_DB, str) or not MONGO_DB.strip():
        raise RuntimeError("MONGO_DB is not configured")
    return get_mongo_client()[MONGO_DB]

def init_indexes(collection_name: str = "articles"):
    """Initialize database indexes. Safe to call multiple times (idempotent)."""
    try:
        db = get_db()
        collection = db[collection_name]
        
        # Create indexes with background=True for better performance
        # urlHash unique index
        collection.create_index(
            [("urlHash", ASCENDING)], 
            unique=True, 
            name="urlHash_unique",
            background=True
        )
        
        # (publishedAt, source) compound index for efficient recent queries
        collection.create_index(
            [("publishedAt", DESCENDING), ("source", ASCENDING)], 
            name="publishedAt_source",
            background=True
        )
        
        # publishedAt index for recent queries
        collection.create_index(
            [("publishedAt", DESCENDING)], 
            name="publishedAt_desc",
            background=True
        )

        # The stock-analysis ingestion contract stores source timestamps as
        # ISO ``publish_date`` strings.  Keep the original ``publishedAt``
        # index for the typed Article model, and index the actively queried
        # compatibility field as well; otherwise every ticker news refresh
        # sorts the collection in memory.
        collection.create_index(
            [("publish_date", DESCENDING)],
            name="publish_date_desc",
            background=True,
        )
        
        # Optional: users.watchlist.tickers (if using user matching later)
        try:
            db.users.create_index(
                [("watchlist.tickers", ASCENDING)], 
                name="watchlist_tickers",
                background=True
            )
        except Exception as e:
            logger.debug(f"Users index creation skipped (optional): {e}")
            
        logger.info("Database indexes initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize indexes: {e}")
        raise

def test_connection():
    """Test MongoDB connection and return database info."""
    try:
        client = get_mongo_client()
        db = get_db()
        
        # Test basic operations
        server_info = client.server_info()
        collections = db.list_collection_names()
        
        return {
            "status": "connected",
            "server_version": server_info.get("version"),
            "database": MONGO_DB,
            "collections": collections
        }
    except Exception as e:
        logger.error(f"MongoDB connection test failed: {e}")
        return {"status": "failed", "error": str(e)}
