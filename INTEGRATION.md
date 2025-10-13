# vynn_core Integration Examples

This document shows how to integrate `vynn_core` with article scrapers and the main application.

## Basic Usage

```python
from vynn_core import Article, init_indexes, upsert_articles, find_recent

# Initialize database (run once)
init_indexes()

# Create article from scraper data
article_data = {
    "url": "https://example.com/nvda-earnings",
    "title": "NVIDIA Reports Strong Q4 Earnings",
    "summary": "Record revenue driven by AI demand...",
    "source": "TechNews",
    "publishedAt": datetime.utcnow(),
    "entities": {"tickers": ["NVDA"], "keywords": ["earnings", "AI"]},
    "quality": {"llmScore": 8.5, "reason": "High relevance"}
}

# Save to database
result = upsert_articles([article_data])
print(f"Created: {len(result['created'])}, Updated: {len(result['updated'])}")

# Retrieve recent articles
recent = find_recent(limit=10)
for article in recent:
    print(f"{article['title']} - {article['source']}")
```

## Integration with Article Scraper

Here's how to modify your existing scraper to use `vynn_core`:

```python
# In your scraper.py or wherever articles are processed

from vynn_core import Article, upsert_articles, init_indexes
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ArticleProcessor:
    def __init__(self):
        # Initialize database indexes once
        init_indexes()
        logger.info("vynn_core database initialized")
    
    def process_scraped_articles(self, scraped_articles):
        """
        Process articles from scraper and save to database.
        
        Args:
            scraped_articles: List of dictionaries with article data
            
        Returns:
            dict: Results from upsert operation
        """
        processed_articles = []
        
        for scraped_data in scraped_articles:
            try:
                # Convert scraped data to vynn_core format
                article_data = self._convert_scraped_data(scraped_data)
                
                # Validate using Pydantic model
                article = Article(**article_data)
                processed_articles.append(article.to_mongo_dict())
                
            except Exception as e:
                logger.error(f"Failed to process article {scraped_data.get('url', 'unknown')}: {e}")
                continue
        
        if processed_articles:
            # Save to database
            result = upsert_articles(processed_articles)
            logger.info(f"Saved articles - Created: {len(result['created'])}, "
                       f"Updated: {len(result['updated'])}, Skipped: {len(result['skipped'])}")
            return result
        else:
            return {"created": [], "updated": [], "skipped": []}
    
    def _convert_scraped_data(self, scraped_data):
        """Convert scraped data to vynn_core Article format."""
        return {
            "url": scraped_data["url"],
            "title": scraped_data["title"],
            "summary": scraped_data.get("summary", ""),
            "source": scraped_data.get("source", "Unknown"),
            "image": scraped_data.get("image"),
            "publishedAt": scraped_data.get("publishedAt", datetime.utcnow()),
            "entities": {
                "tickers": scraped_data.get("tickers", []),
                "keywords": scraped_data.get("keywords", [])
            },
            "quality": {
                "llmScore": scraped_data.get("relevance_score", 5.0),
                "reason": scraped_data.get("relevance_reason", "Scraped article")
            }
        }

# Usage example
processor = ArticleProcessor()

# When your scraper returns articles
scraped_articles = your_scraper.scrape_articles(query="NVDA")
result = processor.process_scraped_articles(scraped_articles)
```

## Pipeline Integration

For your main pipeline, you can integrate like this:

```python
# In your main pipeline
from vynn_core import find_recent, get_articles_by_ids, Article

def search_news_pipeline(ticker: str, limit: int = 50):
    """Enhanced search-news pipeline with database storage."""
    
    # 1. Check database for existing articles
    existing_articles = find_recent(limit=limit, source=None)
    ticker_articles = [
        article for article in existing_articles 
        if ticker in article.get("entities", {}).get("tickers", [])
    ]
    
    if len(ticker_articles) >= limit:
        logger.info(f"Found {len(ticker_articles)} existing articles for {ticker}")
        return ticker_articles
    
    # 2. If not enough articles, scrape new ones
    needed = limit - len(ticker_articles)
    logger.info(f"Scraping {needed} new articles for {ticker}")
    
    # Your existing scraper logic here
    scraped_articles = scraper.search_articles(ticker, limit=needed)
    
    # 3. Process and save new articles
    processor = ArticleProcessor()
    result = processor.process_scraped_articles(scraped_articles)
    
    # 4. Return combined results
    if result["created"] or result["updated"]:
        # Get fresh data including newly created articles
        all_recent = find_recent(limit=limit)
        return [
            article for article in all_recent 
            if ticker in article.get("entities", {}).get("tickers", [])
        ]
    else:
        return ticker_articles

# Usage
articles = search_news_pipeline("NVDA", limit=20)
print(f"Found {len(articles)} articles for NVDA")
```

## Configuration

Make sure to set environment variables:

```bash
export MONGO_URI="mongodb+srv://user:password@cluster.mongodb.net/"
export MONGO_DB="stock-dashboard"
export REDIS_URL="redis://localhost:6379/0"
```

Or update the config file directly:

```python
# In vynn_core/config.py
MONGO_URI = "your-mongodb-connection-string"
MONGO_DB = "your-database-name"
```

## Error Handling

The package includes comprehensive error handling:

```python
from vynn_core import test_connection, upsert_articles
import logging

# Test database connection
connection_status = test_connection()
if connection_status["status"] != "connected":
    logging.error(f"Database connection failed: {connection_status.get('error')}")
    # Handle error or fallback
else:
    logging.info("Database connected successfully")

# Upsert with error handling
try:
    result = upsert_articles(articles)
    logging.info(f"Database operation completed: {result}")
except Exception as e:
    logging.error(f"Failed to save articles: {e}")
    # Handle error or retry
```

## Performance Tips

1. **Batch Operations**: Always use `upsert_articles()` with multiple articles rather than one at a time
2. **Index Usage**: The package creates optimal indexes for common queries
3. **Connection Pooling**: MongoDB client uses connection pooling automatically
4. **URL Deduplication**: URLs are automatically deduplicated using hashes

## Testing

Test your integration:

```python
# Test without database
python test_functionality.py

# Test with database (requires valid MongoDB URI)
python test_mongodb.py
```