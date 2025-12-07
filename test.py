import os
from dotenv import load_dotenv
from trading_agent.agents.data_ingestor import get_account, get_positions, get_bars, get_quotes, get_orders
from trading_agent.agents.indicator_agent import calculate_indicators

# Load environment variables
load_dotenv()

# Check for required API keys
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    print("Missing Alpaca API keys. Please check your .env file.")
    exit(1)

print("Testing data ingestion from Alpaca...")

try:
    # Test account info
    print("\n1. Fetching account information:")
    account = get_account()
    print(f"Account ID: {account.get('id')}")
    print(f"Cash: {account.get('cash')}")
    print(f"Buying Power: {account.get('buying_power')}")
    print(f"Portfolio Value: {account.get('portfolio_value')}")

    # Test positions
    print("\n2. Fetching current positions:")
    positions = get_positions()
    if positions:
        for pos in positions:
            print(f"Symbol: {pos.get('symbol')}, Qty: {pos.get('qty')}, Avg Price: {pos.get('avg_entry_price')}")
    else:
        print("No open positions.")

    # Test bars for AAPL
    print("\n3. Fetching recent bars for AAPL:")
    bars = get_bars("AAPL", timeframe="1Min")
    print(f"Retrieved {len(bars)} bars.")
    if not bars.empty:
        print("Last 5 bars:")
        print(bars.tail(5))
    else:
        print("No bars data retrieved.")

    # Test indicators
    print("\n3b. Calculating indicators for AAPL:")
    indicators = calculate_indicators(bars)
    print("Indicators calculated. Last 5 rows:")
    print(indicators.tail(5))

    # Test quotes for AAPL
    print("\n4. Fetching latest quote for AAPL:")
    quote = get_quotes("AAPL")
    print(f"Full quote response: {quote}")
    quote_data = quote.get('quote', {})
    print(f"Ask Price: {quote_data.get('ap')}, Bid Price: {quote_data.get('bp')}")

    # Test orders
    print("\n5. Fetching open orders:")
    orders = get_orders()
    if orders:
        for order in orders:
            print(f"Order ID: {order.get('id')}, Symbol: {order.get('symbol')}, Qty: {order.get('qty')}, Side: {order.get('side')}")
    else:
        print("No open orders.")

    print("\nData ingestion test completed successfully!")

except Exception as e:
    print(f"Error during testing: {e}")