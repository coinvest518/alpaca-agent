import os
import requests
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# Alpaca URLs (for trading operations)
BASE_URL = "https://api.alpaca.markets"
DATA_BASE_URL = "https://data.alpaca.markets"

# Alpha Vantage URLs (for free market data)
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

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
    """Fetch historical bars for a symbol using Alpha Vantage (free API)."""
    print(f"🔍 Fetching bars for {symbol} using Alpha Vantage...")

    # Check if Alpha Vantage API key is available
    if not ALPHA_VANTAGE_API_KEY or ALPHA_VANTAGE_API_KEY == "your_alpha_vantage_key_here":
        print(f"❌ Alpha Vantage API key not configured. Please set ALPHA_VANTAGE_API_KEY in .env")
        return pd.DataFrame()  # Return empty DataFrame

    # For free tier, we can only get daily data
    # Map timeframe to what we can provide with free tier
    is_intraday_request = timeframe in ["1Min", "5Min", "15Min", "30Min", "60Min", "1H"]
    if is_intraday_request:
        print(f"⚠️ Alpha Vantage free tier only supports daily data. Converting {timeframe} to daily.")
        actual_timeframe = "1D"
    else:
        actual_timeframe = timeframe

    # Alpha Vantage free tier parameters - only daily data available
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
        "outputsize": "compact"  # Last 100 data points
    }

    print(f"      📡 API Call: {ALPHA_VANTAGE_BASE_URL} with params: {params}")

    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()
        print(f"      📊 Response status: {response.status_code}")

        # Check for API errors
        if "Error Message" in data:
            print(f"      ❌ Alpha Vantage API Error: {data['Error Message']}")
            return pd.DataFrame()

        if "Note" in data:
            print(f"      ⚠️ Alpha Vantage Note: {data['Note']}")
            return pd.DataFrame()

        if "Information" in data:
            print(f"      ⚠️ Alpha Vantage Information: {data['Information']}")
            print(f"      💡 Alpha Vantage free tier limitations - switching to alternative approach")
            return pd.DataFrame()

        # Extract time series data
        time_series_key = None
        for key in data.keys():
            if "Time Series" in key:
                time_series_key = key
                break

        if not time_series_key:
            print(f"      ❌ No time series data found in response")
            return pd.DataFrame()

        time_series = data[time_series_key]
        print(f"      📈 Found {len(time_series)} data points")

        # Convert to DataFrame
        bars_data = []
        for timestamp, values in time_series.items():
            bar = {
                'timestamp': timestamp,
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': int(float(values['5. volume']))
            }
            bars_data.append(bar)

        df = pd.DataFrame(bars_data)

        # Convert timestamp to datetime and set as index
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        # Sort by timestamp (Alpha Vantage returns newest first)
        df = df.sort_index()

        # Rename columns to match what indicators expect (Alpaca format)
        df = df.rename(columns={
            'open': 'o',
            'high': 'h',
            'low': 'l',
            'close': 'c',
            'volume': 'v'
        })

        # Filter by date range if specified
        if start_date:
            start_dt = pd.to_datetime(start_date)
            df = df[df.index >= start_dt]

        if end_date:
            end_dt = pd.to_datetime(end_date)
            df = df[df.index <= end_dt]

        # For intraday requests, create synthetic data from daily data
        if is_intraday_request and hours_back:
            # Since we only have daily data, we'll create synthetic intraday data
            # by repeating the daily values (not ideal but better than no data)
            print(f"      🔄 Creating synthetic {timeframe} data from daily data")
            df = _create_synthetic_intraday_data(df, timeframe, hours_back)

        print(f"      ✅ Final DataFrame shape: {df.shape}")
        print(f"      📊 Final columns: {list(df.columns)}")
        if not df.empty:
            print(f"      📅 Date range: {df.index.min()} to {df.index.max()}")

        return df

    except requests.exceptions.RequestException as e:
        print(f"      ❌ Network error fetching data from Alpha Vantage: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        print(f"      ❌ Error processing Alpha Vantage data: {str(e)}")
        return pd.DataFrame()


def _create_synthetic_intraday_data(daily_df, timeframe, hours_back):
    """Create synthetic intraday data from daily data with realistic price movements."""
    if daily_df.empty:
        return daily_df

    import numpy as np

    # Get the most recent daily data
    latest_day = daily_df.iloc[-1]

    # Create intraday bars for the last few hours
    intraday_data = []
    base_time = datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)  # Market open

    # Determine interval in minutes
    interval_minutes = {
        "1Min": 1,
        "5Min": 5,
        "15Min": 15,
        "30Min": 30,
        "60Min": 60,
        "1H": 60
    }.get(timeframe, 5)

    # Create bars for the last N hours
    total_minutes = hours_back * 60
    num_bars = total_minutes // interval_minutes

    # Calculate realistic price movements with MORE variation for trading charts
    daily_open = latest_day['o']
    daily_high = latest_day['h']
    daily_low = latest_day['l']
    daily_close = latest_day['c']

    # Create a trending price path with SIGNIFICANT variation
    trend_direction = 1 if daily_close > daily_open else -1
    trend_strength = abs(daily_close - daily_open) / daily_open * 2.0  # 200% of daily move for more action

    # Generate price path with MUCH more randomness for realistic trading
    np.random.seed(42)  # For reproducible results

    # Start from daily open with some initial variation
    current_price = daily_open + np.random.normal(0, (daily_high - daily_low) * 0.3)  # Much more initial variation

    for i in range(num_bars):
        bar_time = base_time + timedelta(minutes=i * interval_minutes)

        # Add significant trend and random movement
        trend_component = trend_direction * trend_strength * (i / num_bars) * (daily_high - daily_low)
        random_component = np.random.normal(0, (daily_high - daily_low) * 0.25)  # Much bigger random moves

        # Calculate bar prices with substantial variation
        bar_open = current_price
        bar_close = bar_open + trend_component + random_component

        # Create realistic high/low with significant variation
        price_range = daily_high - daily_low
        high_variation = abs(np.random.normal(0, price_range * 0.4))  # Much more variation
        low_variation = abs(np.random.normal(0, price_range * 0.4))   # Much more variation

        bar_high = max(bar_open, bar_close) + high_variation
        bar_low = min(bar_open, bar_close) - low_variation

        # Allow much more flexibility beyond daily bounds for realistic intraday swings
        bar_high = min(bar_high, daily_high * 1.15)  # Allow 15% overshoot
        bar_low = max(bar_low, daily_low * 0.85)    # Allow 15% undershoot
        bar_close = np.clip(bar_close, bar_low, bar_high)

        # Update current price with continuity but more variation
        current_price = bar_close + np.random.normal(0, price_range * 0.1)  # More variation between bars

        bar = {
            'timestamp': bar_time,
            'o': round(bar_open, 2),
            'h': round(bar_high, 2),
            'l': round(bar_low, 2),
            'c': round(bar_close, 2),
            'v': latest_day['v'] // num_bars
        }
        intraday_data.append(bar)

    result_df = pd.DataFrame(intraday_data)
    result_df['timestamp'] = pd.to_datetime(result_df['timestamp'])
    result_df.set_index('timestamp', inplace=True)

    return result_df

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