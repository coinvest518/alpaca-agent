import os
import requests
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
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
    """Fetch historical bars for a symbol."""
    if start_date is None:
        # Default to last N hours instead of 10 days
        start_date = (datetime.now() - timedelta(hours=hours_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {
        "start": start_date,
        "end": end_date,
        "timeframe": timeframe
    }
    response = requests.get(f"{DATA_BASE_URL}/v2/stocks/{symbol}/bars", headers=HEADERS, params=params)
    print(f"      🔍 API Call: {response.url}")
    print(f"      📡 Response Status: {response.status_code}")
    print(f"      📝 Response Content Length: {len(response.text)}")
    print(f"      📄 Response Content Preview: {response.text[:500]}...")

    # Handle subscription limitations (403 errors)
    if response.status_code == 403:
        print(f"      🚫 Subscription limitation: Cannot access market data for {symbol} (403 Forbidden)")
        return pd.DataFrame()  # Return empty DataFrame instead of raising exception

    response.raise_for_status()
    data = response.json()

    # Debug: print response structure
    print(f"   📊 API Response for {symbol}:")
    print(f"      Parsed JSON type: {type(data)}")
    if data is None:
        print(f"      ❌ JSON parsing returned None")
        return pd.DataFrame()  # Return empty DataFrame

    bars_data = data.get('bars')
    print(f"      Bars data type: {type(bars_data)}")
    print(f"      Bars data value: {bars_data}")

    if bars_data is None or (isinstance(bars_data, list) and len(bars_data) == 0):
        print(f"      No bars in response (null or empty)")
        return pd.DataFrame()  # Return empty DataFrame

    print(f"      Bars count: {len(bars_data)}")
    sample = bars_data[0] if bars_data else {}
    print(f"      Sample bar: {sample}")
    print(f"      Available columns: {list(sample.keys()) if sample else 'None'}")

    # Convert to DataFrame
    df = pd.DataFrame(bars_data)

    # Alpaca uses 't' for timestamp, but let's check what we actually get
    timestamp_col = None
    for col in ['t', 'timestamp', 'time']:
        if col in df.columns:
            timestamp_col = col
            break

    if timestamp_col:
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        df.set_index(timestamp_col, inplace=True)
        print(f"      ✅ Using timestamp column: {timestamp_col}")
    else:
        print(f"      ⚠️  No timestamp column found, creating synthetic index")
        # Create a simple index if no timestamp
        df.index = pd.date_range(start=datetime.now() - timedelta(hours=hours_back),
                                periods=len(df), freq='5min')

    print(f"      📈 Final DataFrame shape: {df.shape}")
    print(f"      📊 Final columns: {list(df.columns)}")

    return df

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