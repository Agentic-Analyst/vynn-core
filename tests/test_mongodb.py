#!/usr/bin/env python3
"""
Test script to verify MongoDB connectivity and article operations.
Run this to test the vynn_core package functionality.
"""

import sys
import logging
from datetime import datetime
from pprint import pprint

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mongodb_connection():
    """Test basic MongoDB connection."""
    print("=" * 50)
    print("TESTING MONGODB CONNECTION")
    print("=" * 50)
    
    try:
        from vynn_core.db.mongo import test_connection, init_indexes
        
        # Test connection
        result = test_connection()
        print("Connection test result:")
        pprint(result)
        
        if result["status"] == "connected":
            print("✅ MongoDB connection successful!")
            
            # Initialize indexes
            print("\nInitializing indexes...")
            init_indexes()
            print("✅ Indexes initialized successfully!")
            
            return True
        else:
            print("❌ MongoDB connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing MongoDB connection: {e}")
        return False

def test_article_operations():
    """Test article CRUD operations."""
    print("\n" + "=" * 50)
    print("TESTING ARTICLE OPERATIONS")
    print("=" * 50)
    
    try:
        from vynn_core.dao.articles import upsert_articles, get_articles_by_ids, find_recent, get_article_by_url
        from vynn_core.models import Article
        from vynn_core.utils.time import utc_now
        
        # Create test articles
        test_articles = [
            {
                "url": "https://example.com/nvda-earnings-q4-2024",
                "title": "NVIDIA Reports Strong Q4 2024 Earnings",
                "summary": "NVIDIA exceeded expectations with record revenue driven by AI demand.",
                "source": "TechNews",
                "publishedAt": utc_now(),
                "entities": {"tickers": ["NVDA"], "keywords": ["earnings", "AI", "revenue"]},
                "quality": {"llmScore": 8.5, "reason": "High relevance and recent news"}
            },
            {
                "url": "https://example.com/apple-stock-analysis",
                "title": "Apple Stock Analysis: Is AAPL Still a Buy?",
                "summary": "Comprehensive analysis of Apple's recent performance and future prospects.",
                "source": "MarketWatch",
                "publishedAt": utc_now(),
                "entities": {"tickers": ["AAPL"], "keywords": ["analysis", "stock", "buy"]},
                "quality": {"llmScore": 7.2, "reason": "Good analysis depth"}
            }
        ]
        
        # Test upsert
        print("1. Testing article upsert...")
        result = upsert_articles(test_articles)
        print("Upsert result:")
        pprint(result)
        
        if result["created"]:
            print(f"✅ Created {len(result['created'])} articles")
            
            # Test retrieval by IDs
            print("\n2. Testing retrieval by IDs...")
            retrieved = get_articles_by_ids(result["created"])
            print(f"Retrieved {len(retrieved)} articles:")
            for article in retrieved:
                print(f"  - {article['title']} (ID: {article['_id']})")
            
            # Test duplicate upsert (should skip)
            print("\n3. Testing duplicate upsert (should skip)...")
            duplicate_result = upsert_articles(test_articles)
            print("Duplicate upsert result:")
            pprint(duplicate_result)
            
            if duplicate_result["skipped"]:
                print("✅ Correctly skipped duplicate articles")
            
            # Test recent articles
            print("\n4. Testing recent articles retrieval...")
            recent = find_recent(limit=5)
            print(f"Found {len(recent)} recent articles:")
            for article in recent:
                print(f"  - {article['title']} ({article['publishedAt']})")
            
            # Test get by URL
            print("\n5. Testing get article by URL...")
            test_url = test_articles[0]["url"]
            article_by_url = get_article_by_url(test_url)
            if article_by_url:
                print(f"✅ Found article by URL: {article_by_url['title']}")
            else:
                print("❌ Could not find article by URL")
            
            return True
        else:
            print("❌ No articles were created")
            return False
            
    except Exception as e:
        print(f"❌ Error testing article operations: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pydantic_model():
    """Test Pydantic Article model."""
    print("\n" + "=" * 50)
    print("TESTING PYDANTIC MODEL")
    print("=" * 50)
    
    try:
        from vynn_core.models import Article
        from vynn_core.utils.time import utc_now
        
        # Create article using Pydantic model
        article = Article(
            url="https://test.com/model-test",
            title="Test Article",
            summary="Testing Pydantic model",
            source="TestSource",
            publishedAt=utc_now(),
            entities={"tickers": ["TEST"], "keywords": ["test"]},
            quality={"llmScore": 9.0, "reason": "Test article"}
        )
        
        print("Created Article model:")
        print(f"  URL: {article.url}")
        print(f"  Title: {article.title}")
        print(f"  URL Hash: {article.urlHash}")  # Should be auto-generated
        
        # Test MongoDB dict conversion
        mongo_dict = article.to_mongo_dict()
        print("\nMongoDB dict conversion:")
        pprint(mongo_dict)
        
        print("✅ Pydantic model test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Pydantic model: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧪 Testing vynn_core MongoDB functionality")
    print("Make sure MongoDB is running and accessible!")
    
    success_count = 0
    total_tests = 3
    
    # Test 1: MongoDB Connection
    if test_mongodb_connection():
        success_count += 1
    
    # Test 2: Article Operations  
    if test_article_operations():
        success_count += 1
        
    # Test 3: Pydantic Model
    if test_pydantic_model():
        success_count += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Passed: {success_count}/{total_tests} tests")
    
    if success_count == total_tests:
        print("🎉 All tests passed! vynn_core is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())