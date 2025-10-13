import redis
from ..config import REDIS_URL
from threading import Lock

_redis_client = None
_redis_lock = Lock()

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        with _redis_lock:
            if _redis_client is None:
                _redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client
