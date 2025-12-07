#!/usr/bin/env python3
"""Test script for the scraping agent."""

import os
import sys
from dotenv import load_dotenv

# Add the trading_agent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'trading_agent'))

from trading_agent.agents.scraping_agent import ScrapingAgent

load_dotenv()

def test_scraping_agent():
    """Test the scraping agent functionality."""
    print("🧪 Testing Scraping Agent...")
    print("=" * 50)

    # Check API key
    api_key = os.getenv("HYPERBROWSER_API_KEY")
    print(f"🔑 HYPERBROWSER_API_KEY: {'SET' if api_key else 'NOT SET'}")
    if not api_key:
        print("❌ API key not found!")
        return

    # Initialize scraping agent
    try:
        scraper = ScrapingAgent()
        print("✅ Scraping agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize scraping agent: {e}")
        return

    # Test news scraping for NFGC
    print("\n📰 Testing news scraping for NFGC...")
    try:
        news_data = scraper.scrape_financial_news("NFGC")
        print(f"📊 News data type: {type(news_data)}")
        print(f"📊 News data length: {len(news_data) if isinstance(news_data, list) else 'Not a list'}")

        if isinstance(news_data, list) and len(news_data) > 0:
            print("✅ News data retrieved successfully!")
            for i, item in enumerate(news_data[:3]):  # Show first 3 items
                print(f"  {i+1}. {item.get('title', 'No title')}")
                print(f"     Sentiment: {item.get('sentiment', 'unknown')}")
        else:
            print("❌ No news data retrieved or empty list")

    except Exception as e:
        print(f"❌ Error testing news scraping: {e}")

    # Test market intelligence scraping
    print("\n🌍 Testing market intelligence scraping...")
    try:
        market_data = scraper.scrape_market_data("https://finance.yahoo.com/")
        print(f"📊 Market data type: {type(market_data)}")
        print(f"📊 Market data keys: {list(market_data.keys()) if isinstance(market_data, dict) else 'Not a dict'}")

        if isinstance(market_data, dict) and market_data:
            print("✅ Market intelligence retrieved successfully!")
            for key, value in market_data.items():
                print(f"  {key}: {value[:100] if isinstance(value, str) else value}...")
        else:
            print("❌ No market intelligence retrieved or empty dict")

    except Exception as e:
        print(f"❌ Error testing market intelligence: {e}")

    print("\n" + "=" * 50)
    print("🧪 Scraping Agent Test Complete")

if __name__ == "__main__":
    test_scraping_agent()