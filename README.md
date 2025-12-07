# 🤖 AI Alpaca Trading Agent

An intelligent algorithmic trading system powered by AI, built with Python, Flask, and modern web technologies.

## 🚀 Features

- **AI-Powered Trading**: Uses advanced algorithms and technical indicators for automated trading decisions
- **Real-time Dashboard**: Modern web interface with live market data, charts, and portfolio tracking
- **Technical Analysis**: RSI, EMA, MACD, and volatility indicators
- **Risk Management**: Configurable risk levels and position sizing
- **News Integration**: Market sentiment analysis from news sources
- **Email Notifications**: Automated trading reports and alerts
- **RESTful API**: Full API for integration with other systems

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Pandas, NumPy
- **AI/ML**: LangChain, Google Gemini, Composio
- **Database**: Astra DB (Vector Database)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js
- **APIs**: Alpaca Trading API, LangSmith, HyperBrowser
- **Deployment**: Railway, Docker-ready

## Architecture

```
├── app.py                 # Flask web application
├── main.py               # Command-line trading bot
├── trading_agent/        # Core trading logic
│   ├── coordinator.py    # Main trading workflow
│   ├── agents/          # Individual agents
│   └── ...
├── templates/           # HTML templates
├── static/             # CSS, JS, assets
└── requirements.txt    # Python dependencies
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual API keys
nano .env
```

### 4. Run the Application
```bash
python app.py
```

Visit `http://localhost:5000` to access the dashboard.

## 🔧 Environment Variables

See `.env.example` for all required environment variables. Key variables include:

- `ALPACA_API_KEY` & `ALPACA_SECRET_KEY`: For live trading
- `GOOGLE_API_KEY`: For AI decision making
- `AUTO_START_TRADING`: Set to `true` for automatic startup

## 📊 Dashboard Features

- **Market Overview**: Real-time price charts with technical indicators
- **Portfolio Management**: Live P&L tracking and position monitoring
- **Trading Controls**: Manual and automated trading modes
- **Risk Settings**: Adjustable risk levels and parameters
- **News Feed**: Market intelligence and sentiment analysis
- **Performance Analytics**: Win/loss ratios and trading statistics

## 🚀 Deployment

### Railway (Recommended)
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push

### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ALPACA_API_KEY=your_key
export ALPACA_SECRET_KEY=your_secret
# ... other variables

# Run the app
python app.py
```

### 4. Alternative: Run Command-Line Bot
```bash
python main.py
```

## Web Dashboard Features

### 🏠 **Dashboard Overview**
- **Real-time market charts** with price data
- **Portfolio overview** with P&L tracking
- **Trading status** indicator (Active/Stopped)
- **Quick stats** (Total P&L, Active positions)

### ⚙️ **Controls**
- **Start/Stop Trading**: Control autonomous operation
- **Run Single Cycle**: Execute one trading analysis
- **Trading Settings**: Configure risk levels and modes
- **Timeframe Selection**: View different chart periods

### 📊 **Trading Decisions**
- **AI Recommendations**: HOLD, BUY, SELL decisions
- **Technical Analysis**: Real-time indicator values
- **Decision Reasoning**: Detailed analysis breakdown

### 📰 **Market Intelligence**
- **Live News Feed**: Financial news with sentiment analysis
- **News Impact**: Positive/negative sentiment indicators

### 📈 **Technical Indicators**
- **RSI**: Overbought/oversold signals
- **EMA**: Trend analysis
- **ATR**: Volatility measurement
- **Volatility Score**: Risk assessment

## API Endpoints

- `GET /` - Main dashboard
- `POST /api/start_trading` - Start autonomous trading
- `POST /api/stop_trading` - Stop autonomous trading
- `POST /api/run_cycle` - Execute single trading cycle
- `GET /api/trading_status` - Get current trading status
- `GET /api/market_data` - Get live market data
- `GET /api/portfolio` - Get portfolio information
- `GET /api/news` - Get latest news

## Deployment to Railway

### 1. Prepare for Deployment
```bash
# Install additional dependencies if needed
pip install gunicorn

# Create Procfile for Railway
echo "web: gunicorn app:app" > Procfile
```

### 2. Deploy to Railway
1. Push code to GitHub repository
2. Connect Railway to your GitHub repo
3. Set environment variables in Railway dashboard
4. Deploy automatically

### 3. Railway Configuration
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Environment Variables**: Set all API keys in Railway secrets

## Trading Strategy

The AI trading bot uses a multi-step analysis process:

1. **Data Collection**: Fetches market data from Alpaca API
2. **News Analysis**: Scrapes financial news for sentiment
3. **Technical Analysis**: Calculates RSI, EMA, ATR, volatility
4. **AI Decision Making**: Uses Gemini LLM for final trading decisions
5. **Order Execution**: Places orders through Alpaca API
6. **Email Reporting**: Sends detailed reports via Composio

## Risk Management

- **Position Sizing**: Configurable risk levels
- **Stop Losses**: Automatic loss prevention
- **Diversification**: Multi-symbol analysis
- **News Sentiment**: Avoids trading during negative news events

## Monitoring & Alerts

- **Real-time Dashboard**: Live monitoring of all activities
- **Email Notifications**: Alerts for opportunities and losses
- **Trading Logs**: Detailed execution records
- **Performance Metrics**: P&L tracking and analysis

## Security

- **API Key Management**: Secure environment variable storage
- **Rate Limiting**: Prevents API abuse
- **Error Handling**: Graceful failure recovery
- **Logging**: Comprehensive activity tracking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Disclaimer

This is an educational project. Trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results. Always do your own research and consult with financial advisors before trading.

---

**Built with**: Python, Flask, Chart.js, Bootstrap, Alpaca API, Google Gemini, Composio

Project scaffold is contained in ./langsmith-multilang-agent
See that folder for code, tests, and samples.
