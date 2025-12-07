import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class ScrapingAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_news(self, symbol):
        """Scrape news for a specific symbol with clickable article links."""
        print(f"🔍 Scraping news for {symbol}")
        try:
            import feedparser
            rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
            feed = feedparser.parse(rss_url)

            news_items = []
            for entry in feed.entries[:5]:
                title_lower = entry.title.lower()
                sentiment = self._determine_sentiment(title_lower)

                news_items.append({
                    "title": entry.title,
                    "summary": entry.summary if hasattr(entry, 'summary') else entry.title,
                    "source": entry.source.title if hasattr(entry, 'source') else "Yahoo Finance",
                    "timestamp": entry.published,
                    "sentiment": sentiment,
                    "url": entry.link,
                    "symbol": symbol
                })

            if news_items:
                print(f"📰 Found {len(news_items)} articles for {symbol}")
                return news_items

            print(f"⚠️ No RSS data for {symbol}, using fallback")
            return [{
                "title": f"Market update for {symbol}",
                "summary": f"Recent market developments for {symbol} stock.",
                "source": "Market Data",
                "timestamp": datetime.now().isoformat(),
                "sentiment": "neutral",
                "url": f"https://finance.yahoo.com/quote/{symbol}",
                "symbol": symbol
            }]

        except Exception as e:
            print(f"❌ News scraping failed for {symbol}: {str(e)}")
            return [{
                "title": f"Market data for {symbol}",
                "summary": f"Stock information for {symbol}.",
                "source": "Fallback",
                "timestamp": datetime.now().isoformat(),
                "sentiment": "neutral",
                "url": f"https://finance.yahoo.com/quote/{symbol}",
                "symbol": symbol
            }]

    def _determine_sentiment(self, text):
        """Determine sentiment from text."""
        if any(word in text for word in ["rise", "up", "gain", "bull", "buy", "positive", "surge", "rally"]):
            return "positive"
        elif any(word in text for word in ["fall", "down", "drop", "bear", "sell", "negative", "plunge", "crash"]):
            return "negative"
        return "neutral"

    def scrape_financial_news(self, symbol):
        """Scrape financial news for a specific symbol."""
        return self.scrape_news(symbol)

    def scrape_market_data(self, url):
        """Scrape broader market data from a given URL."""
        try:
            if "yahoo.com" in url:
                response = self.session.get("https://finance.yahoo.com/", timeout=10)
                if response.status_code == 200:
                    content = response.text.lower()
                    sentiment = "neutral"
                    if "market up" in content or "gains" in content:
                        sentiment = "positive"
                    elif "market down" in content or "losses" in content:
                        sentiment = "negative"

                    market_summary = "Market data retrieved from Yahoo Finance"
                    if "spx" in content:
                        market_summary += " - S&P 500 active"
                    if "dow" in content:
                        market_summary += " - Dow Jones trading"

                    return {
                        "market_summary": market_summary,
                        "timestamp": datetime.now().isoformat(),
                        "sentiment": sentiment,
                        "key_levels": ["S&P 500", "Dow Jones", "Nasdaq"],
                        "source": "Yahoo Finance"
                    }

            return {
                "market_summary": "Market data temporarily unavailable - using cached information",
                "timestamp": datetime.now().isoformat(),
                "sentiment": "neutral",
                "key_levels": [],
                "source": "Fallback"
            }

        except Exception as e:
            print(f"❌ Market data scraping failed: {str(e)}")
            return {
                "market_summary": "Market data unavailable",
                "timestamp": datetime.now().isoformat(),
                "sentiment": "neutral"
            }
