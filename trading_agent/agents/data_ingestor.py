import os
import requests
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

# Alpaca URLs (for trading operations and market data)
BASE_URL = "https://api.alpaca.markets"
DATA_BASE_URL = "https://data.alpaca.markets"

HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
}

def get_account():
    """Fetch account information from Alpaca."""
    response = requests.get(f"{BASE_URL}/v2/account", headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_positions():
    """Fetch current positions from Alpaca."""
    response = requests.get(f"{BASE_URL}/v2/positions", headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_bars(symbol, start_date=None, end_date=None, timeframe="5Min", hours_back=2):
    """Fetch historical bars for a symbol using Alpaca free tier (real market data) with database fallback."""
    print(f"🔍 Fetching bars for {symbol} using Alpaca free tier...")

    # Try Alpaca first for real-time data
    alpaca_data = _get_bars_from_alpaca(symbol, start_date, end_date, timeframe, hours_back)

    if alpaca_data is not None and not alpaca_data.empty:
        print(f"✅ Using fresh Alpaca data for {symbol}")
        # Save to database for future use
        _save_bars_to_database(symbol, alpaca_data)
        return alpaca_data

    # Fallback to database if Alpaca fails
    print(f"⚠️ Alpaca data unavailable for {symbol}, checking database...")
    db_data = _get_bars_from_database(symbol, start_date, end_date, timeframe, hours_back)

    if db_data is not None and not db_data.empty:
        print(f"✅ Using saved database data for {symbol}")
        return db_data

    print(f"❌ No data available for {symbol} from Alpaca or database")
    return pd.DataFrame()


def _get_bars_from_alpaca(symbol, start_date=None, end_date=None, timeframe="5Min", hours_back=2):
    """Fetch bars directly from Alpaca API."""
    # Use Alpaca's free tier with IEX feed (real market data)
    if start_date is None:
        # Default to last N hours
        start_date = (datetime.now() - timedelta(hours=hours_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Use IEX feed for free tier (real-time data available)
    params = {
        "start": start_date,
        "end": end_date,
        "timeframe": timeframe,
        "feed": "iex"  # Free tier: IEX exchange (real market data)
    }

    try:
        response = requests.get(f"{DATA_BASE_URL}/v2/stocks/{symbol}/bars", headers=HEADERS, params=params)
        print(f"      📡 API Call: {response.url}")
        print(f"      📊 Response Status: {response.status_code}")

        if response.status_code == 403:
            print(f"      🚫 Subscription limitation detected for {symbol}")
            print(f"      💡 Alpaca free tier provides IEX data only (2.5% of market volume)")
            print(f"      🔄 Falling back to available data...")
            # Try without feed parameter to get whatever is available
            params.pop("feed", None)
            response = requests.get(f"{DATA_BASE_URL}/v2/stocks/{symbol}/bars", headers=HEADERS, params=params)
            print(f"      📡 Fallback API Call: {response.url}")
            print(f"      📊 Fallback Response Status: {response.status_code}")

        response.raise_for_status()
        data = response.json()

        # Debug: print response structure
        print(f"      📝 Response keys: {list(data.keys()) if data else 'None'}")

        bars_data = data.get('bars')
        if bars_data is None or (isinstance(bars_data, list) and len(bars_data) == 0):
            print(f"      ⚠️ No bars data available for {symbol}")
            return pd.DataFrame()  # Return empty DataFrame

        print(f"      📈 Found {len(bars_data)} real market data bars")

        # Convert to DataFrame
        df = pd.DataFrame(bars_data)

        # Alpaca uses 't' for timestamp
        if 't' in df.columns:
            df['t'] = pd.to_datetime(df['t'])
            df.set_index('t', inplace=True)
            print(f"      ✅ Using timestamp column 't'")
        else:
            print(f"      ⚠️ No timestamp column found")
            # Create synthetic timestamps if needed
            df.index = pd.date_range(start=datetime.now() - timedelta(hours=hours_back),
                                    periods=len(df), freq='5min')

        # Rename columns to match what indicators expect (Alpaca format)
        df = df.rename(columns={
            'o': 'o',  # open
            'h': 'h',  # high
            'l': 'l',  # low
            'c': 'c',  # close
            'v': 'v'   # volume
        })

        # Filter by date range if specified
        if start_date:
            start_dt = pd.to_datetime(start_date)
            df = df[df.index >= start_dt]

        if end_date:
            end_dt = pd.to_datetime(end_date)
            df = df[df.index <= end_dt]

        print(f"      ✅ Final DataFrame shape: {df.shape}")
        print(f"      📊 Final columns: {list(df.columns)}")
        if not df.empty:
            print(f"      📅 Date range: {df.index.min()} to {df.index.max()}")

        return df

    except requests.exceptions.RequestException as e:
        print(f"      ❌ Network error fetching data from Alpaca: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        print(f"      ❌ Error processing Alpaca data: {str(e)}")
        return pd.DataFrame()


def _save_bars_to_database(symbol, data):
    """Save market data to database for future use."""
    try:
        from .storage_agent import trading_storage
        trading_storage.save_market_data(symbol, data)
        print(f"      💾 Saved {len(data)} bars for {symbol} to database")
    except Exception as e:
        print(f"      ⚠️ Failed to save data to database: {e}")


def _get_bars_from_database(symbol, start_date=None, end_date=None, timeframe="5Min", hours_back=2):
    """Retrieve market data from database as fallback."""
    try:
        from .storage_agent import trading_storage

        # Convert timeframe to appropriate limit
        timeframe_limits = {
            "1Min": 1440,  # 24 hours of 1-min bars
            "5Min": 288,   # 24 hours of 5-min bars
            "15Min": 96,   # 24 hours of 15-min bars
            "30Min": 48,   # 24 hours of 30-min bars
            "1H": 168,     # 7 days of hourly bars
            "1D": 365      # 1 year of daily bars
        }
        limit = timeframe_limits.get(timeframe, 288)

        data = trading_storage.get_market_data(symbol, start_date, limit)

        if data is not None and not data.empty:
            print(f"      📚 Retrieved {len(data)} bars for {symbol} from database")
            return data

        print(f"      📭 No saved data found for {symbol} in database")
        return pd.DataFrame()

    except Exception as e:
        print(f"      ❌ Error retrieving data from database: {e}")
        return pd.DataFrame()


def get_quotes(symbol):
    """Fetch latest quotes for a symbol."""
    response = requests.get(f"{DATA_BASE_URL}/v2/stocks/{symbol}/quotes/latest", headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_orders():
    """Fetch all orders."""
    response = requests.get(f"{BASE_URL}/v2/orders", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_order(order_id):
    """Fetch a specific order."""
    response = requests.get(f"{BASE_URL}/v2/orders/{order_id}", headers=HEADERS)
    response.raise_for_status()
    return response.json()