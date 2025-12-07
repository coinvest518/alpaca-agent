# Code Changes Required

## 1. Update dashboard.js - renderNews Method

**Location**: `static/js/dashboard.js` (around line 800-850)

**Find this code**:
```javascript
renderNews(newsData) {
    const container = document.getElementById('news-feed');
    let html = '';

    // newsData should be in the format {symbol: [news_items]}
    Object.keys(newsData).forEach(symbol => {
        const newsItems = newsData[symbol];
        if (Array.isArray(newsItems)) {
            newsItems.slice(0, 5).forEach(item => {
                const title = item.title || 'No title';
                const summary = item.summary || 'No summary';
                const sentiment = item.sentiment || 'neutral';

                // Special styling for market intelligence
                if (symbol === 'MARKET_INTELLIGENCE') {
                    html += `
                        <div class="news-item market-intelligence ${sentiment}">
                            <div class="news-title"><i class="fas fa-chart-line me-2"></i>${title}</div>
                            <div class="news-summary">${summary.length > 150 ? summary.substring(0, 150) + '...' : summary}</div>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="news-item ${sentiment}">
                            <div class="news-title">${symbol}: ${title}</div>
                            <div class="news-summary">${summary.length > 100 ? summary.substring(0, 100) + '...' : summary}</div>
                        </div>
                    `;
                }
            });
        }
    });

    if (!html) {
        html = '<div class="text-center text-muted"><i class="fas fa-search fa-2x mb-3 opacity-50"></i><p>Scanning for market news...</p><small class="text-muted">Real-time news and analysis</small></div>';
    }

    container.innerHTML = html;
}
```

**Replace with this code**:
```javascript
renderNews(newsData) {
    const container = document.getElementById('news-feed');
    let html = '';

    Object.keys(newsData).forEach(symbol => {
        const newsItems = newsData[symbol];
        if (Array.isArray(newsItems)) {
            newsItems.slice(0, 5).forEach(item => {
                const title = item.title || 'No title';
                const summary = item.summary || 'No summary';
                const sentiment = item.sentiment || 'neutral';
                const url = item.url || '#';
                const source = item.source || 'Market Data';

                if (symbol === 'MARKET_INTELLIGENCE') {
                    html += `
                        <a href="${url}" target="_blank" class="news-item market-intelligence ${sentiment} text-decoration-none">
                            <div class="news-title"><i class="fas fa-chart-line me-2"></i>${title}</div>
                            <div class="news-summary">${summary.length > 150 ? summary.substring(0, 150) + '...' : summary}</div>
                            <div class="news-meta"><small>${source}</small></div>
                        </a>
                    `;
                } else {
                    html += `
                        <a href="${url}" target="_blank" class="news-item ${sentiment} text-decoration-none">
                            <div class="news-title">${symbol}: ${title}</div>
                            <div class="news-summary">${summary.length > 100 ? summary.substring(0, 100) + '...' : summary}</div>
                            <div class="news-meta"><small>${source}</small></div>
                        </a>
                    `;
                }
            });
        }
    });

    if (!html) {
        html = '<div class="text-center text-muted"><i class="fas fa-search fa-2x mb-3 opacity-50"></i><p>Scanning for market news...</p><small class="text-muted">Real-time news and analysis</small></div>';
    }

    container.innerHTML = html;
}
```

**Key Changes**:
- Changed `<div>` to `<a>` tag
- Added `href="${url}"` for clickable links
- Added `target="_blank"` to open in new tab
- Added `class="text-decoration-none"` to remove underline
- Added `<div class="news-meta">` for source display
- Extract `url` and `source` from news item

---

## 2. Update index.html - Add CSS Link

**Location**: `templates/index.html` (in `<head>` section, after other CSS links)

**Find this line**:
```html
<link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet">
```

**Add after it**:
```html
<link href="{{ url_for('static', filename='css/news_styles.css') }}" rel="stylesheet">
```

**Full section should look like**:
```html
<head>
    <!-- ... other head content ... -->
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome Icons -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <!-- Custom CSS -->
    <link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/news_styles.css') }}" rel="stylesheet">
</head>
```

---

## 3. Create news_styles.css

**Location**: `static/css/news_styles.css` (NEW FILE)

**Content**:
```css
/* News Item Enhancements - Clickable Links */

.news-item {
    display: block;
    color: inherit;
    text-decoration: none;
    cursor: pointer;
}

.news-item:hover {
    text-decoration: none;
}

.news-meta {
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    font-size: 0.75rem;
    color: var(--text-muted);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.news-meta small {
    opacity: 0.7;
}

.news-meta::after {
    content: '→';
    font-weight: bold;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.news-item:hover .news-meta::after {
    opacity: 1;
}

/* Sentiment-based styling */
.news-item.positive .news-title {
    color: #00ff88;
}

.news-item.negative .news-title {
    color: #ff4757;
}

.news-item.neutral .news-title {
    color: #b8c5d6;
}

.news-item.market-intelligence .news-title {
    color: #00d4ff;
}

/* Link hover effects */
.news-item:hover .news-title {
    text-decoration: underline;
    text-decoration-color: currentColor;
    text-underline-offset: 4px;
}
```

---

## 4. Update scraping_agent.py

**Location**: `trading_agent/agents/scraping_agent.py`

**Replace entire file with**:
```python
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
```

---

## Summary of Changes

### Files to Modify
1. ✅ `static/js/dashboard.js` - Update renderNews() method
2. ✅ `templates/index.html` - Add CSS link
3. ✅ `trading_agent/agents/scraping_agent.py` - Enhance scraping

### Files to Create
1. ✅ `static/css/news_styles.css` - New CSS file

### Files Already Working (No Changes Needed)
- `app.py` - Already returns news with URLs
- `trading_agent/coordinator.py` - Already scrapes for all symbols
- `trading_agent/agents/astra_db_agent.py` - Already stores data

---

## Testing Checklist

- [ ] Update scraping_agent.py
- [ ] Update dashboard.js renderNews() method
- [ ] Create news_styles.css
- [ ] Add CSS link to index.html
- [ ] Start Flask app: `python app.py`
- [ ] Open dashboard: `http://localhost:5000`
- [ ] Check "Market Intelligence" section
- [ ] Verify news items display
- [ ] Click on news item
- [ ] Verify article opens in new tab
- [ ] Check sentiment colors (green/red/gray/blue)
- [ ] Verify source attribution shows
- [ ] Test with multiple symbols

---

## Deployment

1. **Backup existing files**:
   ```bash
   cp static/js/dashboard.js static/js/dashboard.js.bak
   cp trading_agent/agents/scraping_agent.py trading_agent/agents/scraping_agent.py.bak
   ```

2. **Apply changes**:
   - Update dashboard.js
   - Update scraping_agent.py
   - Create news_styles.css
   - Update index.html

3. **Test locally**:
   ```bash
   python app.py
   ```

4. **Deploy to production**:
   ```bash
   git add .
   git commit -m "Add clickable news links with sentiment analysis"
   git push
   ```

5. **Monitor**:
   - Check logs for errors
   - Verify news displays correctly
   - Test article links
   - Monitor performance
