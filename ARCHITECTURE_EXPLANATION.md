# AI Alpaca Trading System - Architecture Explanation

## System Overview

The AI Alpaca Trading System is a multi-agent trading bot that analyzes account positions and makes intelligent trading decisions. Here's how all components work together:

### Data Flow

```
1. ACCOUNT POSITIONS (Alpaca API)
   ↓
2. SCRAPING AGENT (HyperBrowser)
   - Scrapes news for ALL symbols in positions + orders
   - Scrapes market intelligence (broader market data)
   - Saves reference data to Astra DB
   ↓
3. COORDINATOR (LangGraph)
   - Orchestrates the trading workflow
   - Runs 5 sequential steps
   ↓
4. DASHBOARD (Flask + JavaScript)
   - Displays real-time data
   - Shows news with clickable links
   - Displays technical indicators
   - Shows AI decisions
```

## File Structure & Responsibilities

### Backend Files

#### `app.py` - Flask Web Server
- **Purpose**: Main web application and API endpoints
- **Key Endpoints**:
  - `/api/news` - Returns news for ALL account positions + market intelligence
  - `/api/market_data` - Returns current prices for all symbols
  - `/api/portfolio` - Returns portfolio summary
  - `/api/historical_data/<symbol>` - Returns chart data
- **Flow**: Initializes scraping agent → calls `/api/news` → returns formatted data to frontend

#### `trading_agent/coordinator.py` - Trading Workflow Orchestrator
- **Purpose**: Manages the 5-step trading cycle using LangGraph
- **Steps**:
  1. `get_account_positions` - Fetches positions, orders, account balance
  2. `analyze_positions` - For each position:
     - Gets market data (bars)
     - Calculates technical indicators
     - **Scrapes news for that symbol**
     - **Scrapes market intelligence**
     - Saves data to Astra DB
  3. `make_position_decisions` - Uses LLM to decide: BUY, SELL, HOLD, etc.
  4. `execute_actions` - Places orders based on decisions
  5. `log_actions` - Saves trades to Astra DB + sends email
- **Key Feature**: Parallel processing of multiple positions using ThreadPoolExecutor

#### `trading_agent/agents/scraping_agent.py` - News & Market Data Scraper
- **Purpose**: Scrapes financial news and market intelligence
- **Methods**:
  - `scrape_news(symbol)` - Gets news for a specific symbol
    - Uses Yahoo Finance RSS feed
    - Extracts title, summary, sentiment, URL
    - **Returns clickable article links**
  - `scrape_market_data(url)` - Gets broader market intelligence
    - Scrapes market sentiment
    - Gets key market levels
    - Returns market overview
- **Data Saved**: News items with URLs stored in Astra DB

#### `trading_agent/agents/data_ingestor.py` - Market Data Fetcher
- **Purpose**: Fetches real market data from Alpaca API
- **Key Functions**:
  - `get_positions()` - Current holdings
  - `get_orders()` - Pending orders
  - `get_bars(symbol, timeframe, hours_back)` - Historical price data
  - Fallback to Astra DB if Alpaca fails

#### `trading_agent/agents/astra_db_agent.py` - Vector Database
- **Purpose**: Persistent storage for trading data
- **Collections**:
  - `trades` - Trade history and decisions
  - `market_data` - Historical price bars
  - `indicators` - Technical indicators (RSI, MACD, EMA, etc.)
- **Key Methods**:
  - `save_market_data(symbol, data)` - Stores price bars
  - `save_indicators(symbol, indicators)` - Stores calculated indicators
  - `get_market_data(symbol)` - Retrieves cached data
  - `get_performance_summary()` - Returns trading statistics

#### `trading_agent/agents/storage_agent.py` - Storage Interface
- **Purpose**: Wrapper around Astra DB for trading operations
- **Bridges**: Coordinator ↔ Astra DB communication

### Frontend Files

#### `templates/index.html` - Dashboard HTML
- **Sections**:
  - Portfolio Overview (positions table)
  - Market Data Chart (with timeframe selector)
  - AI Trading Decisions
  - Technical Indicators (RSI, MACD, EMA, Volatility)
  - **Market Intelligence** (news feed with clickable links)
  - Performance Overview
- **Key Elements**:
  - `#news-feed` - Container for news items
  - Each news item has a clickable URL link

#### `static/js/dashboard.js` - Frontend Logic
- **Key Classes**:
  - `DashboardManager` - Main controller
  - Handles API calls to Flask backend
  - Updates UI with real-time data
- **Key Methods**:
  - `loadNews()` - Fetches news from `/api/news`
  - `displayNews(newsData)` - Renders news items with clickable links
  - `loadMarketData()` - Fetches prices and chart data
  - `updatePortfolio()` - Refreshes portfolio display

#### `static/css/style.css` - Styling
- Dashboard styling and responsive layout

## Data Flow for News Integration

### Current Implementation (What We Have)

1. **Coordinator Step 2** (`analyze_positions`):
   ```python
   for each position:
       scraper.scrape_news(symbol)  # Get news for this symbol
       scraper.scrape_market_data()  # Get market intelligence
       save to Astra DB
   ```

2. **App.py `/api/news` endpoint**:
   ```python
   for each position symbol:
       get news from scraper
       format as {symbol: [news_items]}
   return to frontend
   ```

3. **Dashboard.js `loadNews()`**:
   ```javascript
   fetch('/api/news')
   for each symbol:
       display news items with title, sentiment, URL
   ```

### What We're Adding

**Enhanced Scraping Logic**:
- Scrape news for ALL symbols in positions + orders (already done in coordinator)
- Include clickable article URLs in news items (already in scraper)
- Display news with working links in UI (need to add to dashboard)

**Enhanced Dashboard Display**:
- Show news items with clickable links
- Each link redirects to the actual article
- Display sentiment indicators (positive/negative/neutral)
- Show source and timestamp

## Key Integration Points

### 1. Scraping Agent → Coordinator
```python
# In coordinator.py analyze_single_position()
news_data = scraper.scrape_financial_news(symbol)
market_intelligence = scraper.scrape_market_data(url)
# Saved in analysis_results[symbol]
```

### 2. Coordinator → Astra DB
```python
# In coordinator.py log_actions()
trading_storage.save_market_data(symbol, bars)
trading_storage.save_indicators(symbol, indicators)
# News is included in trading_data for email
```

### 3. Astra DB → Flask API
```python
# In app.py /api/news endpoint
# Retrieves news from scraper (which may use cached data)
# Returns formatted JSON to frontend
```

### 4. Flask API → Dashboard
```javascript
// In dashboard.js loadNews()
fetch('/api/news')
.then(response => response.json())
.then(data => displayNews(data))
```

### 5. Dashboard → User
```html
<!-- News item with clickable link -->
<a href="article_url" target="_blank">
  <h6>Article Title</h6>
  <p>Article Summary</p>
</a>
```

## How News Scraping Works

### Step 1: Identify All Symbols
```python
# In coordinator.py get_account_positions()
positions = get_positions()  # Get account holdings
orders = get_orders()        # Get pending orders
symbols = [pos['symbol'] for pos in positions]
```

### Step 2: Scrape News for Each Symbol
```python
# In coordinator.py analyze_single_position()
for symbol in symbols:
    news = scraper.scrape_news(symbol)
    # Returns: [{title, summary, sentiment, url, timestamp, source}, ...]
```

### Step 3: Extract Article Links
```python
# In scraping_agent.py scrape_news()
for entry in feed.entries:
    news_items.append({
        'title': entry.title,
        'url': entry.link,  # <-- Clickable link
        'sentiment': determine_sentiment(entry.title),
        ...
    })
```

### Step 4: Display in Dashboard
```javascript
// In dashboard.js displayNews()
for each symbol:
    for each news item:
        create <a href="url" target="_blank">
        display title, summary, sentiment
```

## Astra DB Collections

### trades Collection
```json
{
  "_id": "trade_2024-01-15T10:30:00_AAPL",
  "timestamp": "2024-01-15T10:30:00",
  "symbol": "AAPL",
  "decision": "BUY",
  "indicators": {rsi: 35, macd: 0.5, ...},
  "account_balance": 50000,
  "order_result": {...}
}
```

### market_data Collection
```json
{
  "_id": "bars_AAPL_2024-01-15T10:00:00",
  "symbol": "AAPL",
  "timestamp": "2024-01-15T10:00:00",
  "open": 150.25,
  "high": 151.50,
  "low": 150.00,
  "close": 150.75,
  "volume": 1000000
}
```

### indicators Collection
```json
{
  "_id": "indicators_AAPL_2024-01-15T10:00:00",
  "symbol": "AAPL",
  "timestamp": "2024-01-15T10:00:00",
  "rsi": 45.5,
  "macd": 0.25,
  "ema_20": 150.50,
  "volatility": 0.015
}
```

## Summary

The system works as follows:

1. **Coordinator** orchestrates the trading cycle
2. **Scraping Agent** gathers news for ALL account symbols
3. **Data Ingestor** fetches market data from Alpaca
4. **Astra DB** stores all historical data
5. **Flask API** serves data to the frontend
6. **Dashboard** displays news with clickable links to articles

The key enhancement is that news is scraped for ALL symbols in positions and orders, not just one, and each news item includes a clickable URL that redirects to the actual article.
