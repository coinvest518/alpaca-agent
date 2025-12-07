import os
import requests
from dotenv import load_dotenv

load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"

HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
}

def place_order(symbol, qty, side, type="market", time_in_force="gtc", 
                limit_price=None, stop_price=None, trail_price=None, 
                trail_percent=None, order_class="simple", 
                take_profit=None, stop_loss=None, extended_hours=False):
    """Place an order with full Alpaca order type support."""
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": type,
        "time_in_force": time_in_force,
        "order_class": order_class
    }
    
    # Add optional parameters based on order type
    if limit_price is not None:
        data["limit_price"] = limit_price
    if stop_price is not None:
        data["stop_price"] = stop_price
    if trail_price is not None:
        data["trail_price"] = trail_price
    if trail_percent is not None:
        data["trail_percent"] = trail_percent
    if extended_hours:
        data["extended_hours"] = True
    
    # Handle advanced order classes
    if order_class in ["bracket", "oco", "oto"]:
        if take_profit:
            data["take_profit"] = take_profit
        if stop_loss:
            data["stop_loss"] = stop_loss
    
    response = requests.post(f"{BASE_URL}/v2/orders", headers=HEADERS, json=data)
    response.raise_for_status()
    return response.json()

def place_bracket_order(symbol, qty, side, entry_price, take_profit_price, stop_loss_price, time_in_force="gtc"):
    """Place a bracket order: entry + take-profit + stop-loss."""
    take_profit = {"limit_price": take_profit_price}
    stop_loss = {"stop_price": stop_loss_price}
    
    return place_order(
        symbol=symbol,
        qty=qty,
        side=side,
        type="limit" if side == "buy" else "limit",
        time_in_force=time_in_force,
        limit_price=entry_price,
        order_class="bracket",
        take_profit=take_profit,
        stop_loss=stop_loss
    )

def place_oco_order(symbol, qty, take_profit_price, stop_loss_price, time_in_force="gtc"):
    """Place OCO order: take-profit + stop-loss for existing position."""
    take_profit = {"limit_price": take_profit_price}
    stop_loss = {"stop_price": stop_loss_price}
    
    return place_order(
        symbol=symbol,
        qty=qty,
        side="sell",  # OCO is for closing positions
        type="limit",
        time_in_force=time_in_force,
        order_class="oco",
        take_profit=take_profit,
        stop_loss=stop_loss
    )

def place_trailing_stop(symbol, qty, side, trail_price=None, trail_percent=None, time_in_force="day"):
    """Place a trailing stop order."""
    return place_order(
        symbol=symbol,
        qty=qty,
        side=side,
        type="trailing_stop",
        time_in_force=time_in_force,
        trail_price=trail_price,
        trail_percent=trail_percent
    )

def place_limit_order(symbol, qty, side, limit_price, time_in_force="gtc"):
    """Place a limit order."""
    return place_order(
        symbol=symbol,
        qty=qty,
        side=side,
        type="limit",
        time_in_force=time_in_force,
        limit_price=limit_price
    )

def place_stop_order(symbol, qty, side, stop_price, time_in_force="gtc"):
    """Place a stop order."""
    return place_order(
        symbol=symbol,
        qty=qty,
        side=side,
        type="stop",
        time_in_force=time_in_force,
        stop_price=stop_price
    )

def place_stop_limit_order(symbol, qty, side, stop_price, limit_price, time_in_force="gtc"):
    """Place a stop-limit order."""
    return place_order(
        symbol=symbol,
        qty=qty,
        side=side,
        type="stop",
        time_in_force=time_in_force,
        stop_price=stop_price,
        limit_price=limit_price
    )