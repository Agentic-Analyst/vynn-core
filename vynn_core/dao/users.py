# User DAO - Simplified for future extension
from ..db.mongo import get_db
from ..utils.time import utc_now
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def match_user_ids_for_article(entities: Dict) -> List[str]:
    """
    Match user IDs based on article entities (tickers, keywords).
    This is a placeholder for future user matching functionality.
    """
    # For now, return empty list as user system is not implemented
    # In the future, this would query users collection for watchlist matches
    return []

def create_test_user(user_id: str, watchlist_tickers: List[str]) -> bool:
    """Create a test user for development/testing purposes."""
    try:
        db = get_db()
        user_doc = {
            "_id": user_id,
            "watchlist": {"tickers": watchlist_tickers},
            "createdAt": utc_now(),
        }
        db.users.insert_one(user_doc)
        logger.info(f"Created test user: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to create test user: {e}")
        return False
