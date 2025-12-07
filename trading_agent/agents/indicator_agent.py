import pandas as pd
import numpy as np

def calculate_ema(data, period=20):
    """Calculate Exponential Moving Average."""
    return data.ewm(span=period, adjust=False).mean()

def calculate_rsi(data, period=14):
    """Calculate Relative Strength Index."""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(data, period=14):
    """Calculate Average True Range."""
    high_low = data['h'] - data['l']
    high_close = np.abs(data['h'] - data['c'].shift())
    low_close = np.abs(data['l'] - data['c'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr

def calculate_volatility_score(data, period=14):
    """Calculate a simple volatility score based on ATR normalized by price."""
    atr = calculate_atr(data, period)
    volatility = atr / data['c'] * 100  # Percentage
    return volatility

def calculate_indicators(data):
    """Calculate all indicators for the data."""
    if data.empty:
        print("      📊 No data available for indicator calculation")
        return data  # Return empty DataFrame as-is
    
    data = data.copy()
    data['ema'] = calculate_ema(data['c'], 20)
    data['rsi'] = calculate_rsi(data['c'], 14)
    data['atr'] = calculate_atr(data, 14)
    data['volatility_score'] = calculate_volatility_score(data, 14)
    return data