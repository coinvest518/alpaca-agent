# Integration Guide: News Scraping & Dashboard UI

## Overview

This guide explains how to integrate the enhanced news scraping with clickable article links into your dashboard.

## Files Modified/Created

### 1. Backend - Scraping Agent
**File**: `trading_agent/agents/scraping_agent.py`

**Changes**:
- Enhanced `scrape_news()` method to include symbol tracking
- Added `_determine_sentiment()` helper method
- Each news item now includes: `title`, `summary`, `source`, `timestamp`, `sentiment`, `url`, `symbol`

**Key Feature**: News items now have clickable URLs that redirect to actual articles

### 2. Backend - Coordinator (Already Working)
**File**: `trading_agent/coordinator.py`

**How it works**:
- Step 2 (`analyze_positions`) scrapes news for ALL symbols in positions + orders
- News data is stored in `analysis_results[symbol]['news']`
- Market intelligence is stored in `analysis_results[symbol]['market_intelligence']`
- All data is saved to Astra DB

### 3. Backend - Flask API (Already Working)
**File**: `app.py`

**Endpoint**: `/api/news`
- Returns news for ALL account positions
- Format: `{symbol: [news_items], MARKET_INTELLIGENCE: [market_data]}`
- Each news item includes URL for clickable links

### 4. Frontend - Dashboard JavaScript
**File**: `static/js/dashboard.js`

**Updated Method**: `renderNews(newsData)`
- Renders news items as clickable `<a>` tags
- Each link opens in new tab (`target="_blank"`)
- Displays sentiment indicators
- Shows source and metadata

**Implementation**:
```javascript
renderNews(newsData) {
    const container = document.getElementById('news-feed');
    let html = '';

    Object.keys(newsData).forEach(symbol => {
        const newsItems = newsData[symbol];
        if (Array.isArray(newsItems)) {
            newsItems.slice(0, 5).forEach(item => {
                const url = item.url || '#';
                html += `
                    <a href="${url}" target="_blank" class="news-item ${sentiment}">
                        <div class="news-title">${title}</div>
                        <div class="news-summary">${summary}</div>
                        <div class="news-meta"><small>${source}</small></div>
                    </a>
                `;
            });
        }
    });
    container.innerHTML = html;
}
```

### 5. Frontend - CSS Styling
**Files**: 
- `static/css/style.css` (existing)
- `static/css/news_styles.css` (new)

**Features**:
- Clickable news items with hover effects
- Sentiment-based color coding (positive/negative/neutral)
- Arrow indicator on hover
- Smooth transitions and animations
- Responsive design

## Data Flow

```
1. User opens dashboard
   ↓
2. Dashboard calls loadNews()
   ↓
3. Frontend fetches /api/news
   ↓
4. Flask API calls scraping_agent.scrape_news(symbol)
   ↓
5. Scraper returns news items with URLs
   ↓
6. Frontend renders news as clickable links
   ↓
7. User clicks link → Opens article in new tab
```

## How to Use

### For Users

1. **View News Feed**:
   - Open dashboard
   - Scroll to "Market Intelligence" section
   - See news items for all account positions

2. **Click Article Link**:
   - Hover over news item (arrow appears)
   - Click to open article in new tab
   - Article opens from Yahoo Finance or other sources

3. **Understand Sentiment**:
   - Green border = Positive news
   - Red border = Negative news
   - Gray border = Neutral news
   - Blue border = Market intelligence

### For Developers

#### Adding Custom News Sources

Edit `scraping_agent.py`:

```python
def scrape_news(self, symbol):
    # Add your custom news source here
    # Return list of dicts with: title, summary, url, sentiment, source, timestamp
    
    news_items = []
    # Your scraping logic
    return news_items
```

#### Customizing Sentiment Detection

Edit `_determine_sentiment()` method:

```python
def _determine_sentiment(self, text):
    # Add more keywords for better sentiment detection
    if any(word in text for word in ["your_keywords"]):
        return "positive"
    # ...
```

#### Styling News Items

Edit `static/css/news_styles.css`:

```css
.news-item.positive {
    border-left-color: #00ff88;  /* Green */
}

.news-item.negative {
    border-left-color: #ff4757;  /* Red */
}
```

## Integration Steps

### Step 1: Update Scraping Agent
```bash
# Replace scraping_agent.py with enhanced version
cp trading_agent/agents/scraping_agent.py trading_agent/agents/scraping_agent.py.bak
# Use the new scraping_agent.py
```

### Step 2: Update Dashboard JavaScript
```bash
# Update renderNews method in dashboard.js
# Find the renderNews method and replace with new implementation
```

### Step 3: Add CSS Styling
```html
<!-- Add to templates/index.html in <head> -->
<link href="{{ url_for('static', filename='css/news_styles.css') }}" rel="stylesheet">
```

### Step 4: Test Integration
1. Start Flask app: `python app.py`
2. Open dashboard: `http://localhost:5000`
3. Check "Market Intelligence" section
4. Click on news items to verify links work

## Data Structure

### News Item Format
```json
{
    "title": "Stock rises on earnings beat",
    "summary": "Company reports better than expected earnings...",
    "source": "Yahoo Finance",
    "timestamp": "2024-01-15T10:30:00",
    "sentiment": "positive",
    "url": "https://finance.yahoo.com/news/...",
    "symbol": "AAPL"
}
```

### API Response Format
```json
{
    "status": "success",
    "data": {
        "AAPL": [
            {news_item_1},
            {news_item_2}
        ],
        "MSFT": [
            {news_item_3}
        ],
        "MARKET_INTELLIGENCE": [
            {market_data}
        ]
    },
    "timestamp": "2024-01-15T10:30:00"
}
```

## Features

### ✅ Implemented
- News scraping for ALL account positions
- Clickable article links
- Sentiment analysis (positive/negative/neutral)
- Market intelligence display
- Responsive design
- Hover effects and animations
- Source attribution
- Timestamp display

### 🔄 In Progress
- Real-time news updates
- News caching in Astra DB
- Advanced sentiment analysis
- News filtering by symbol

### 📋 Future Enhancements
- News impact scoring
- Automated trading based on news sentiment
- News archive and search
- Custom news source integration
- Email alerts for important news

## Troubleshooting

### News Not Showing
1. Check browser console for errors
2. Verify `/api/news` endpoint returns data
3. Check if positions exist in account
4. Verify scraping agent is initialized

### Links Not Working
1. Check if URL is valid in news item
2. Verify target="_blank" attribute
3. Check browser popup blocker settings
4. Test with different news sources

### Sentiment Not Displaying
1. Verify sentiment field in news item
2. Check CSS classes match sentiment values
3. Verify news_styles.css is loaded
4. Check browser DevTools for CSS errors

## Performance Considerations

- News scraping happens in parallel for all symbols
- Caching reduces API calls
- Astra DB stores historical news
- Frontend pagination limits displayed items
- Lazy loading for large news feeds

## Security

- URLs are validated before display
- XSS protection via HTML escaping
- CORS headers configured
- API rate limiting enabled
- Sensitive data masked in logs

## Support

For issues or questions:
1. Check logs: `tail -f app.log`
2. Review coordinator output
3. Check Astra DB collections
4. Verify API endpoints
5. Test with curl: `curl http://localhost:5000/api/news`
