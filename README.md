# vynn_core

Minimal, production-ready news feed data layer for MongoDB/Redis.

## Features
- 🗄️ Singleton Mongo/Redis clients with connection pooling
- 📰 Article upsert, dedupe, and retrieval with URL hashing
- 👥 User matching by watchlist (extensible)
- 📡 Feed fan-out with Redis ZADD
- ✅ Pydantic schema validation for articles
- 🔄 Idempotent index creation and operations
- 🧪 Comprehensive testing with mongomock support

## Quick Start

### Installation
```bash
pip install -e libs/vynn_core
```

### Configuration
Set environment variables or update `vynn_core/config.py`:
```bash
export MONGO_URI="mongodb+srv://username:password@cluster.mongodb.net/"
export MONGO_DB="your-database-name"
export REDIS_URL="redis://localhost:6379/0"
```

### Basic Usage
```python
from vynn_core import Article, init_indexes, upsert_articles, find_recent
from datetime import datetime

# Initialize database (run once)
init_indexes()

# Create and save articles
articles = [{
    "url": "https://example.com/nvda-earnings",
    "title": "NVIDIA Reports Strong Q4 Earnings",
    "summary": "Record revenue driven by AI chip demand...",
    "source": "TechNews",
    "publishedAt": datetime.utcnow(),
    "entities": {"tickers": ["NVDA"], "keywords": ["earnings", "AI"]},
    "quality": {"llmScore": 8.5, "reason": "High relevance and recent news"}
}]

result = upsert_articles(articles)
print(f"Created: {len(result['created'])}, Updated: {len(result['updated'])}")

# Retrieve recent articles
recent = find_recent(limit=10)
for article in recent:
    print(f"{article['title']} - {article['source']}")
```

## Integration with Article Scrapers

```python
from vynn_core import Article, upsert_articles

# Process scraped articles
def process_scraped_articles(scraped_data_list):
    articles = []
    for data in scraped_data_list:
        # Convert to vynn_core format
        article = Article(
            url=data["url"],
            title=data["title"],
            summary=data["summary"],
            source=data["source"],
            publishedAt=data["published_at"],
            entities={"tickers": data.get("tickers", []), "keywords": data.get("keywords", [])},
            quality={"llmScore": data.get("score", 5.0), "reason": "Scraped content"}
        )
        articles.append(article.to_mongo_dict())
    
    # Save to database with automatic deduplication
    return upsert_articles(articles)

# Use in your scraper
result = process_scraped_articles(your_scraped_articles)
```

## API Reference

### Core Functions
- `init_indexes()` - Initialize database indexes (idempotent)
- `test_connection()` - Test MongoDB connectivity
- `upsert_articles(docs)` - Save articles with deduplication
- `get_articles_by_ids(ids)` - Retrieve articles by ObjectId
- `find_recent(limit, source)` - Get recent articles
- `get_article_by_url(url)` - Find article by URL

### Models
- `Article` - Pydantic model with auto URL hashing
- Auto-generates `urlHash` from URL (UTM params removed)
- Validates data structure and types

### Utilities
- `url_hash(url)` - Generate SHA256 hash from clean URL
- `utc_now()` - Get current UTC datetime

## Testing

### Without Database
```bash
python test_functionality.py
```

### With MongoDB
```bash
python test_mongodb.py
```

## Database Schema

### Articles Collection
```javascript
{
  "_id": ObjectId,
  "url": "https://example.com/article",
  "urlHash": "sha256_hash_of_clean_url", // Unique index
  "title": "Article Title",
  "summary": "Article summary...",
  "source": "Source Name",
  "image": "https://example.com/image.jpg", // Optional
  "publishedAt": ISODate,
  "entities": {
    "tickers": ["NVDA", "AAPL"],
    "keywords": ["earnings", "AI"]
  },
  "quality": {
    "llmScore": 8.5,
    "reason": "High relevance and recent news"
  },
  "createdAt": ISODate,
  "updatedAt": ISODate
}
```

### Indexes
- `urlHash` (unique) - For deduplication
- `publishedAt, source` (compound) - For recent queries
- `publishedAt` (descending) - For time-based queries

## Error Handling

The package includes comprehensive error handling and logging:
- Connection failures are logged and re-raised
- Invalid articles are skipped with logging
- Duplicate key errors are handled gracefully
- All database operations include try-catch blocks

## Performance Notes

- Uses MongoDB connection pooling
- Batch operations for efficiency
- Background index creation
- URL normalization removes UTM parameters
- Automatic deduplication by URL hash

For detailed integration examples, see [INTEGRATION.md](INTEGRATION.md).
