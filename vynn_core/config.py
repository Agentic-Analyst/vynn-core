import os

# Database configuration - loaded from .env file
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

# Redis configuration (used by feed fan-out). Defaults to a local Redis; in
# Docker deployments this is overridden via REDIS_URL (e.g. redis://redis:6379).
# Without this, `from ..config import REDIS_URL` in db/redis.py raised ImportError.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
