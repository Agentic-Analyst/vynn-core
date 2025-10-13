from ..db.redis import get_redis_client

def push(article_id: str, user_ids: list[str], score: float = None):
    r = get_redis_client()
    for uid in user_ids:
        r.zadd(f"feed:{uid}", {article_id: score or 0})
