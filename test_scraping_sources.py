import os
from dotenv import load_dotenv
from langchain_hyperbrowser import HyperbrowserScrapeTool

load_dotenv()

HYPERBROWSER_API_KEY = os.getenv("HYPERBROWSER_API_KEY")

def test_scraping_approaches():
    """Test different scraping approaches for news."""
    if not HYPERBROWSER_API_KEY:
        print("❌ HYPERBROWSER_API_KEY not found")
        return

    scraper = HyperbrowserScrapeTool(api_key=HYPERBROWSER_API_KEY)

    # Test different URLs and approaches
    test_cases = [
        {
            "name": "Yahoo Finance NFGC",
            "url": "https://finance.yahoo.com/quote/NFGC/news",
            "description": "Current approach with stock symbol"
        },
        {
            "name": "Yahoo Finance with company name",
            "url": "https://finance.yahoo.com/quote/NFGC?p=NFGC",
            "description": "Yahoo with NFGC parameter"
        },
        {
            "name": "Google News NFGC",
            "url": "https://www.google.com/search?q=NFGC+stock+news&tbm=nws",
            "description": "Google News search for NFGC"
        },
        {
            "name": "Bing News NFGC",
            "url": "https://www.bing.com/news/search?q=NFGC+stock+news",
            "description": "Bing News search for NFGC"
        },
        {
            "name": "Yahoo Finance general news",
            "url": "https://finance.yahoo.com/news/",
            "description": "Yahoo Finance general news page"
        },
        {
            "name": "MarketWatch NFGC",
            "url": "https://www.marketwatch.com/investing/stock/nfGC",
            "description": "MarketWatch page for NFGC"
        }
    ]

    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"📍 URL: {test_case['url']}")
        print(f"📝 Description: {test_case['description']}")

        try:
            result = scraper.run({
                "url": test_case['url'],
                "scrape_options": {"formats": ["markdown"]}
            })

            if result and 'markdown' in result:
                content = result['markdown']
                print(f"✅ Success! Content length: {len(content)} characters")

                # Show first few lines
                lines = content.split('\n')[:10]
                print("📄 Content preview:")
                for i, line in enumerate(lines):
                    if line.strip():
                        print(f"  {i+1}: {line[:100]}...")

                # Try to extract news-like content
                news_lines = [line for line in content.split('\n') if len(line.strip()) > 20 and not line.startswith('#')]
                print(f"📊 Found {len(news_lines)} potential news lines")

            else:
                print("❌ No markdown content returned")
                print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")

        except Exception as e:
            print(f"❌ Error: {e}")

        print("-" * 50)

if __name__ == "__main__":
    test_scraping_approaches()