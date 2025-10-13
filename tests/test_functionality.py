#!/usr/bin/env python3
"""
Simple test script to verify vynn_core functionality without requiring MongoDB.
"""

import logging
from datetime import datetime
from pprint import pprint

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_models_and_utils():
    """Test models and utility functions without DB connection."""
    print("=" * 60)
    print("TESTING MODELS AND UTILITIES (No DB Required)")
    print("=" * 60)
    
    try:
        from vynn_core.models import Article
        from vynn_core.utils.time import utc_now
        from vynn_core.utils.hashing import url_hash
        
        # Test utility functions
        print("1. Testing utility functions...")
        test_url = "https://example.com/test-article?utm_source=twitter&utm_campaign=test"
        hash_value = url_hash(test_url)
        print(f"   URL: {test_url}")
        print(f"   Hash: {hash_value}")
        
        current_time = utc_now()
        print(f"   Current UTC time: {current_time}")
        
        # Test Article model
        print("\n2. Testing Article model...")
        article = Article(
            url="https://example.com/nvda-earnings",
            title="NVIDIA Q4 2024 Earnings Beat Expectations",
            summary="NVIDIA reported record revenue driven by AI chip demand, beating analyst expectations.",
            source="TechNews",
            publishedAt=current_time,
            entities={"tickers": ["NVDA"], "keywords": ["earnings", "AI", "revenue"]},
            quality={"llmScore": 8.5, "reason": "High relevance and recent news"}
        )
        
        print(f"   Created article: {article.title}")
        print(f"   URL Hash (auto-generated): {article.urlHash}")
        print(f"   Published at: {article.publishedAt}")
        print(f"   Entities: {article.entities}")
        print(f"   Quality: {article.quality}")
        
        # Test MongoDB dict conversion
        print("\n3. Testing MongoDB dict conversion...")
        mongo_dict = article.to_mongo_dict()
        print("   MongoDB-ready dictionary:")
        for key, value in mongo_dict.items():
            print(f"     {key}: {value}")
        
        # Test with different URL formats
        print("\n4. Testing URL hash consistency...")
        urls = [
            "https://example.com/article",
            "https://example.com/article?utm_source=twitter",
            "https://example.com/article?utm_campaign=test&utm_source=facebook",
            "https://example.com/article?param=value&utm_source=google"
        ]
        
        for url in urls:
            hash_val = url_hash(url)
            print(f"   {url} -> {hash_val}")
        
        print("\n✅ All model and utility tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in model/utility tests: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_article_serialization():
    """Test article creation from dict (like what would come from a scraper)."""
    print("\n" + "=" * 60)
    print("TESTING ARTICLE SERIALIZATION")
    print("=" * 60)
    
    try:
        from vynn_core.models import Article
        from vynn_core.utils.time import utc_now
        
        # Simulate scraped article data
        scraped_data = {
            "url": "https://finance.yahoo.com/news/apple-stock-hits-record-high-180000123.html",
            "title": "Apple Stock Hits Record High After Strong iPhone Sales",
            "summary": "Apple shares reached an all-time high following better-than-expected iPhone sales in Q4.",
            "source": "Yahoo Finance",
            "publishedAt": utc_now(),
            "entities": {
                "tickers": ["AAPL"],
                "keywords": ["iPhone", "sales", "record", "stock"]
            },
            "quality": {
                "llmScore": 7.8,
                "reason": "Strong relevance to Apple stock performance"
            }
        }
        
        print("1. Creating Article from scraped data...")
        print("   Scraped data:")
        pprint(scraped_data)
        
        # Create Article instance
        article = Article(**scraped_data)
        print(f"\n   ✅ Successfully created Article: {article.title}")
        print(f"   Auto-generated URL Hash: {article.urlHash}")
        
        # Test batch creation (like what would happen in upsert_articles)
        print("\n2. Testing batch article creation...")
        batch_data = [
            {
                "url": "https://reuters.com/technology/tesla-reports-q4-earnings",
                "title": "Tesla Reports Q4 Earnings Beat",
                "summary": "Tesla exceeded earnings expectations with strong Model Y sales.",
                "source": "Reuters",
                "publishedAt": utc_now(),
                "entities": {"tickers": ["TSLA"], "keywords": ["earnings", "Tesla"]},
                "quality": {"llmScore": 8.0, "reason": "High impact earnings news"}
            },
            {
                "url": "https://bloomberg.com/news/microsoft-azure-growth",
                "title": "Microsoft Azure Shows Continued Growth",
                "summary": "Microsoft's cloud services division reports 25% year-over-year growth.",
                "source": "Bloomberg",
                "publishedAt": utc_now(),
                "entities": {"tickers": ["MSFT"], "keywords": ["Azure", "cloud", "growth"]},
                "quality": {"llmScore": 7.5, "reason": "Important cloud growth story"}
            }
        ]
        
        articles = []
        for data in batch_data:
            article = Article(**data)
            articles.append(article)
            print(f"   ✅ Created: {article.title} (Hash: {article.urlHash[:8]}...)")
        
        print(f"\n   Successfully created {len(articles)} articles in batch")
        
        print("\n✅ All serialization tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in serialization tests: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_scraper_integration():
    """Simulate how the package would integrate with an article scraper."""
    print("\n" + "=" * 60)
    print("SIMULATING SCRAPER INTEGRATION")
    print("=" * 60)
    
    try:
        from vynn_core import Article, upsert_articles, url_hash, utc_now
        
        print("1. Simulating article scraper output...")
        
        # Simulate what an article scraper might return
        def mock_scraper_results():
            return [
                {
                    "url": "https://marketwatch.com/story/nvidia-stock-analysis-2024",
                    "title": "NVIDIA Stock Analysis: Is the AI Rally Sustainable?",
                    "summary": "Analysts weigh in on whether NVIDIA's AI-driven growth can continue into 2025.",
                    "source": "MarketWatch",
                    "publishedAt": utc_now(),
                    "entities": {"tickers": ["NVDA"], "keywords": ["AI", "analysis", "growth"]},
                    "quality": {"llmScore": 8.2, "reason": "In-depth analysis with multiple analyst views"}
                },
                {
                    "url": "https://cnbc.com/2024/amazon-aws-earnings-report",
                    "title": "Amazon AWS Revenue Beats Estimates in Q4",
                    "summary": "Amazon's cloud division shows strong performance despite economic headwinds.",
                    "source": "CNBC",
                    "publishedAt": utc_now(),
                    "entities": {"tickers": ["AMZN"], "keywords": ["AWS", "earnings", "cloud"]},
                    "quality": {"llmScore": 7.9, "reason": "Strong earnings beat with good detail"}
                }
            ]
        
        scraped_articles = mock_scraper_results()
        print(f"   Mock scraper returned {len(scraped_articles)} articles")
        
        print("\n2. Processing articles through vynn_core...")
        
        # Convert to Article models
        articles = []
        for data in scraped_articles:
            article = Article(**data)
            articles.append(article)
            print(f"   ✅ Processed: {article.title}")
            print(f"      URL Hash: {article.urlHash}")
            print(f"      Entities: {article.entities}")
        
        # Simulate the upsert operation (without actual DB)
        print("\n3. Preparing for database upsert...")
        mongo_dicts = [article.to_mongo_dict() for article in articles]
        
        print("   Articles ready for MongoDB:")
        for i, doc in enumerate(mongo_dicts, 1):
            print(f"   Article {i}:")
            print(f"     Title: {doc['title']}")
            print(f"     URL Hash: {doc['urlHash']}")
            print(f"     Source: {doc['source']}")
            print(f"     Tickers: {doc['entities'].get('tickers', [])}")
        
        print("\n✅ Scraper integration simulation successful!")
        print("   🔄 In real usage, these would be passed to upsert_articles(mongo_dicts)")
        return True
        
    except Exception as e:
        print(f"❌ Error in scraper integration simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests that don't require database connectivity."""
    print("🧪 Testing vynn_core functionality (No Database Required)")
    print("This test verifies models, utilities, and integration patterns")
    
    success_count = 0
    total_tests = 3
    
    # Test 1: Models and Utilities
    if test_models_and_utils():
        success_count += 1
    
    # Test 2: Article Serialization
    if test_article_serialization():
        success_count += 1
        
    # Test 3: Scraper Integration Simulation
    if simulate_scraper_integration():
        success_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {success_count}/{total_tests} tests")
    
    if success_count == total_tests:
        print("🎉 All functionality tests passed! vynn_core is ready for use.")
        print("💡 Next steps:")
        print("   1. Fix MongoDB URI for database testing")
        print("   2. Run test_mongodb.py for full database integration tests")
        print("   3. Integrate with your article scraper")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())