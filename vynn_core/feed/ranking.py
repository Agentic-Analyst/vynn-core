def compute_score(article: dict, user_id: str, now_ts: float) -> float:
    # Example: score = llmScore * recency_decay
    llm_score = article.get("quality", {}).get("llmScore", 0)
    published_at = article.get("publishedAt")
    if hasattr(published_at, "timestamp"):
        age = max(1, now_ts - published_at.timestamp())
    else:
        age = 1
    recency_decay = 1.0 / age
    return llm_score * recency_decay
