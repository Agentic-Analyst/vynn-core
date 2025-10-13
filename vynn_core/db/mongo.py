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
