from flask import Flask, render_template, jsonify, request
import os
import json
import time
from datetime import datetime
import threading

app = Flask(__name__)

# Global variables for trading state
trading_coordinator = None
email_agent = None
scraping_agent = None
trading_thread = None
is_trading_active = False
last_trading_data = None

def start_trading_background():
    """Start trading in background thread for auto-start functionality"""
    global is_trading_active, trading_thread

    if not is_trading_active:
        is_trading_active = True
        trading_thread = threading.Thread(target=continuous_trading_loop, daemon=True)
        trading_thread.start()
        print("🤖 Background trading started")

def initialize_agents():
    """Initialize trading agents"""
    global trading_coordinator, email_agent, scraping_agent

    if trading_coordinator is None:
        # Import here to avoid startup issues
        from trading_agent.coordinator import run_trading_cycle
        trading_coordinator = run_trading_cycle

    if email_agent is None:
        # Import here to avoid startup issues
        from trading_agent.agents.email_agent import EmailAgent
        email_agent = EmailAgent()

    if scraping_agent is None:
        # Import here to avoid startup issues
        from trading_agent.agents.scraping_agent import ScrapingAgent
        scraping_agent = ScrapingAgent()

def run_trading_cycle():
    """Run a single trading cycle"""
    global last_trading_data

    try:
        print("🤖 Starting AI Trading Cycle...")
        trading_data = trading_coordinator()
        last_trading_data = trading_data

        # Send email report
        if email_agent and trading_data:
            email_agent.send_trading_report(trading_data)

        print("✅ Trading cycle completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Trading cycle failed: {str(e)}")
        return False

def continuous_trading_loop():
    """Continuous trading loop for autonomous operation"""
    global is_trading_active

    while is_trading_active:
        try:
            run_trading_cycle()
            # Wait 5 minutes between cycles (adjust as needed)
            time.sleep(300)
        except Exception as e:
            print(f"❌ Continuous trading error: {str(e)}")
            time.sleep(60)  # Shorter wait on error

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/start_trading')
def start_trading():
    """Start continuous trading"""
    global is_trading_active, trading_thread

    if not is_trading_active:
        is_trading_active = True
        # Start trading in a background thread
        trading_thread = threading.Thread(target=continuous_trading_loop, daemon=True)
        trading_thread.start()

    return jsonify({'status': 'started', 'message': 'Continuous trading started'})

@app.route('/api/stop_trading')
def stop_trading():
    """Stop continuous trading"""
    global is_trading_active

    is_trading_active = False
    return jsonify({'status': 'stopped', 'message': 'Continuous trading stopped'})

@app.route('/api/run_cycle')
def run_single_cycle():
    """Run a single trading cycle"""
    success = run_trading_cycle()
    return jsonify({
        'status': 'success' if success else 'error',
        'message': 'Trading cycle completed' if success else 'Trading cycle failed'
    })

@app.route('/api/trading_status')
def get_trading_status():
    """Get current trading status"""
    return jsonify({
        'is_active': is_trading_active,
        'last_update': datetime.now().isoformat(),
        'last_data': last_trading_data
    })

@app.route('/api/market_data')
def get_market_data():
    """Get current market data for a specific symbol or all positions"""
    try:
        # Import here to avoid startup issues
        from trading_agent.agents.data_ingestor import get_positions, get_bars, get_orders

        # Check if a specific symbol is requested
        symbol_param = request.args.get('symbol')

        if symbol_param:
            # Fetch data for specific symbol
            symbols_to_fetch = [symbol_param.upper()]
        else:
            # Get positions to know which symbols to fetch data for
            positions = get_positions()
            symbols_to_fetch = [pos.get('symbol') for pos in positions if pos.get('symbol')]

        market_data = {}
        orders = get_orders()  # Get orders for fallback price data
        order_dict = {order['symbol']: order for order in orders}

        for symbol in symbols_to_fetch:
            current_price = None
            volume = 1000  # Default volume
            subscription_limited = False

            # Try 1H bars first (most reliable for volume data)
            print(f"Getting 1H bars for {symbol}...")
            try:
                bars = get_bars(symbol, hours_back=24, timeframe="1H")
                print(f"1H bars result: {bars is not None}, empty: {bars.empty if bars is not None else 'N/A'}")
                if bars is not None and not bars.empty:
                    latest_bar = bars.iloc[-1]
                    volume = int(latest_bar['v'])
                    current_price = float(latest_bar['c'])
                    print(f"Using 1H data: volume={volume}, price={current_price}")
            except Exception as e:
                error_msg = str(e)
                if "403" in error_msg or "subscription does not permit" in error_msg:
                    print(f"⚠️  Subscription limitation detected for {symbol}: {error_msg}")
                    subscription_limited = True

                    # Try older data (7 days ago) which might be available
                    try:
                        print(f"Trying older data (7 days) for {symbol}...")
                        bars = get_bars(symbol, hours_back=168, timeframe="1D")  # 7 days of daily data
                        if bars is not None and not bars.empty:
                            latest_bar = bars.iloc[-1]
                            volume = int(latest_bar['v'])
                            current_price = float(latest_bar['c'])
                            print(f"Using 7-day old data: volume={volume}, price={current_price}")
                    except Exception as e2:
                        print(f"Even older data failed: {e2}")
                else:
                    print(f"Other error getting bars: {error_msg}")

            # If we still don't have price data, use fallbacks
            if current_price is None:
                # First, check if this is a position
                positions = get_positions()
                for pos in positions:
                    if pos.get('symbol') == symbol:
                        current_price = pos.get('current_price')
                        print(f"Using position price: {current_price}")
                        break

                # If not a position, check if there's an open order with limit price
                if current_price is None and symbol in order_dict:
                    order = order_dict[symbol]
                    if order.get('limit_price'):
                        current_price = float(order['limit_price'])
                        print(f"Using order limit price: {current_price}")

                # Last resort: use a demo price for development
                if current_price is None:
                    current_price = 100.0  # Demo price
                    print(f"Using demo price: {current_price}")

            if current_price is not None:
                market_data[symbol] = {
                    'price': float(current_price),
                    'volume': volume,
                    'timestamp': datetime.now().isoformat(),
                    'open': float(current_price),
                    'high': float(current_price),
                    'low': float(current_price),
                    'change_24h': None,  # Will be calculated by frontend
                    'change_percent_24h': None,
                    'subscription_limited': subscription_limited
                }

        return jsonify({
            'status': 'success',
            'data': market_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error in market_data API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': {},
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/symbols')
def get_symbols():
    """Get list of symbols from current positions and open orders"""
    try:
        from trading_agent.agents.data_ingestor import get_positions, get_orders

        positions = get_positions()
        position_symbols = [pos.get('symbol') for pos in positions if pos.get('symbol')]

        # Get open orders
        orders = get_orders()
        order_symbols = [order.get('symbol') for order in orders if order.get('symbol') and order.get('status') in ['accepted', 'pending', 'new']]

        # Combine position symbols with order symbols, removing duplicates
        all_symbols = list(set(position_symbols + order_symbols))
        
        # Sort with position symbols first, then order symbols
        all_symbols.sort(key=lambda x: (x not in position_symbols, x not in order_symbols, x))

        return jsonify({
            'status': 'success',
            'symbols': all_symbols,
            'position_symbols': position_symbols,
            'order_symbols': order_symbols,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'symbols': [],  # No fallback symbols
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/historical_data/<symbol>')
def get_historical_data(symbol):
    """Get historical data for a specific symbol for charting"""
    try:
        from trading_agent.agents.data_ingestor import get_bars

        # Determine timeframe and hours back based on query params
        timeframe = request.args.get('timeframe', '5Min')
        hours_back = int(request.args.get('hours', 24))  # Default 24 hours

        bars = get_bars(symbol, hours_back=hours_back, timeframe=timeframe)

        # Always return success - even with empty data (subscription limitations)
        historical_data = []
        if bars is not None and not bars.empty:
            # Convert to format suitable for Chart.js
            for index, row in bars.iterrows():
                historical_data.append({
                    'timestamp': index.isoformat() if hasattr(index, 'isoformat') else str(index),
                    'open': float(row['o']),
                    'high': float(row['h']),
                    'low': float(row['l']),
                    'close': float(row['c']),
                    'volume': int(row['v'])
                })

        return jsonify({
            'status': 'success',
            'symbol': symbol,
            'data': historical_data,  # Will be empty array if no data available
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error in historical_data API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': [],
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/portfolio')
def get_portfolio():
    """Get portfolio data with full position details"""
    try:
        # Import here to avoid startup issues
        from trading_agent.agents.data_ingestor import get_account, get_positions

        account = get_account()
        positions = get_positions()

        print(f"DEBUG: Got {len(positions) if positions else 0} positions")

        # Calculate portfolio totals
        total_market_value = 0
        total_cost_basis = 0
        total_unrealized_pl = 0

        if positions:
            for pos in positions:
                try:
                    market_value = float(pos.get('market_value', 0))
                    cost_basis = float(pos.get('cost_basis', 0))
                    unrealized_pl = float(pos.get('unrealized_pl', 0))

                    print(f"DEBUG: Position {pos.get('symbol')}: mv={market_value}, cb={cost_basis}, pl={unrealized_pl}")

                    total_market_value += market_value
                    total_cost_basis += cost_basis
                    total_unrealized_pl += unrealized_pl
                except (ValueError, TypeError) as e:
                    print(f"DEBUG: Error processing position: {e}")
                    continue

        print(f"DEBUG: Totals - mv={total_market_value}, cb={total_cost_basis}, pl={total_unrealized_pl}")

        portfolio_data = {
            'account': account,
            'positions': positions or [],
            'summary': {
                'total_market_value': round(total_market_value, 2),
                'total_cost_basis': round(total_cost_basis, 2),
                'total_unrealized_pl': round(total_unrealized_pl, 2),
                'total_unrealized_plpc': round((total_unrealized_pl / total_cost_basis * 100) if total_cost_basis > 0 else 0, 2),
                'position_count': len(positions) if positions else 0
            },
            'timestamp': datetime.now().isoformat()
        }

        print(f"DEBUG: Portfolio data keys: {list(portfolio_data.keys())}")

        return jsonify({
            'status': 'success',
            'data': portfolio_data
        })
    except Exception as e:
        print(f"ERROR in get_portfolio: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/news')
def get_news():
    """Get latest news and market intelligence data"""
    try:
        print(f"🤖 News API called, scraping_agent: {scraping_agent is not None}")
        if scraping_agent:
            # Import here to avoid startup issues
            from trading_agent.agents.data_ingestor import get_positions

            # Get news for current positions
            positions = get_positions()
            news_data = {}
            market_intelligence = None

            if positions:
                symbols = [pos.get('symbol') for pos in positions if pos.get('symbol')]
                print(f"📊 Found positions: {symbols}")

                # Get news for ALL symbols in positions, not just the first one
                for symbol in symbols:
                    try:
                        print(f"📰 Scraping news for {symbol}...")
                        symbol_news = scraping_agent.scrape_news(symbol)
                        if symbol_news:
                            news_data[symbol] = symbol_news
                            print(f"✅ Got {len(symbol_news)} news items for {symbol}")
                        else:
                            print(f"⚠️ No news found for {symbol}")
                    except Exception as e:
                        print(f"❌ Error scraping news for {symbol}: {e}")
                        # Continue with other symbols even if one fails

            # Always get market intelligence
            try:
                print("🔍 Scraping market intelligence...")
                market_intelligence = scraping_agent.scrape_market_data("https://finance.yahoo.com/")
                print(f"✅ Market intelligence scraped: {market_intelligence is not None}")
            except Exception as e:
                print(f"❌ Market intelligence scraping failed: {e}")

            if news_data or market_intelligence:
                # Format data as expected by frontend: {symbol: [news_items]}
                formatted_data = {}

                # Add news for each symbol
                for symbol, news_items in news_data.items():
                    formatted_data[symbol] = news_items

                # Add market intelligence as a special entry
                if market_intelligence:
                    print("📈 Adding market intelligence to response")
                    formatted_data['MARKET_INTELLIGENCE'] = [{
                        'title': f"Market Sentiment: {market_intelligence.get('sentiment', 'neutral').title()}",
                        'summary': market_intelligence.get('market_summary', 'Market data unavailable'),
                        'source': market_intelligence.get('source', 'Market Data'),
                        'timestamp': market_intelligence.get('timestamp', datetime.now().isoformat()),
                        'sentiment': market_intelligence.get('sentiment', 'neutral'),
                        'url': 'https://finance.yahoo.com/'
                    }]

                print(f"📤 Returning data with keys: {list(formatted_data.keys())}")
                return jsonify({
                    'status': 'success',
                    'data': formatted_data,
                    'timestamp': datetime.now().isoformat()
                })

        # No fallback mock data - scraping agent handles fallbacks
        print("⚠️ No scraping agent or no data")
        return jsonify({
            'status': 'success',
            'data': {},
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ News API error: {e}")
        # Return empty data instead of mock data
        return jsonify({
            'status': 'success',
            'data': {},
            'timestamp': datetime.now().isoformat()
        })

if __name__ == '__main__':
    initialize_agents()

    # Auto-start trading on deployment (optional - set to False for manual control)
    AUTO_START_TRADING = os.getenv('AUTO_START_TRADING', 'false').lower() == 'true'

    if AUTO_START_TRADING:
        print("🚀 Auto-starting trading system...")
        from app import start_trading_background
        start_trading_background()
        print("✅ Trading system started automatically")

    # Railway provides PORT environment variable
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)