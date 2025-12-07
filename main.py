# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from trading_agent.coordinator import run_trading_cycle
from trading_agent.agents.storage_agent import trading_storage

# Load environment variables
load_dotenv()

# Check for required API keys
required_keys = ['GOOGLE_API_KEY', 'LANGSMITH_API_KEY', 'LANGCHAIN_API_KEY', 'ALPACA_API_KEY', 'ALPACA_SECRET_KEY', 'ASTRA_DB_API_ENDPOINT', 'ASTRA_DB_APPLICATION_TOKEN']
missing_keys = [key for key in required_keys if not os.getenv(key)]
if missing_keys:
    print(f'Missing required environment variables: {missing_keys}')
    exit(1)

print('All API keys loaded successfully.')

# Test Astra DB connection
try:
    from trading_agent.agents.astra_db_agent import astra_db
    # Test connection by getting recent trades
    test_trades = astra_db.get_recent_trades(1)
    print('Astra DB connection successful.')
except Exception as e:
    print(f'Astra DB connection failed: {e}')
    print('Continuing with local storage only...')

# Run the trading cycle
if __name__ == '__main__':
    symbol = 'AAPL'  # You can change this or make it configurable

    print("=== TRADING STORAGE STATUS ===")
    performance = trading_storage.get_performance_summary()
    print(f"Total trades: {performance.get('total_trades', 0)}")
    print(f"Buy decisions: {performance.get('buy_decisions', 0)}")
    print(f"Sell decisions: {performance.get('sell_decisions', 0)}")
    print(f"Hold decisions: {performance.get('hold_decisions', 0)}")
    print(f"Total P&L: ${performance.get('total_pnl', 0):.2f}")
    print(f"Win rate: {performance.get('win_rate', 0):.1f}%")

    # Show Astra DB data if available
    try:
        recent_trades = trading_storage.get_recent_trades(3)
        if recent_trades:
            print(f"\nRecent Astra DB trades: {len(recent_trades)} found")
            for trade in recent_trades[-2:]:  # Show last 2
                print(f"  {trade.get('symbol')} - {trade.get('decision')} at {trade.get('timestamp')}")
    except Exception as e:
        print(f"Astra DB query failed: {e}")

    print("\n=== RUNNING TRADING CYCLE ===")
    result = run_trading_cycle()
    print('Trading cycle completed.')

    # Show results for each position analyzed
    if result.get('decisions'):
        print(f"Decisions made for {len(result['decisions'])} positions:")
        for symbol, decision_data in result['decisions'].items():
            print(f"  {symbol}: {decision_data['decision']}")

    if result.get('actions_taken'):
        print(f"Actions taken for {len(result['actions_taken'])} positions:")
        for symbol, action in result['actions_taken'].items():
            print(f"  {symbol}: {action['action']}")

    print("\n=== MEMORY CONTEXT ===")
    memory = trading_storage.get_memory_context()
    print(f"Recent memory: {memory[:200]}...")

    print("\n=== UPDATED PERFORMANCE ===")
    updated_performance = trading_storage.get_performance_summary()
    print(f"Total trades: {updated_performance.get('total_trades', 0)}")
    print(f"Total P&L: ${updated_performance.get('total_pnl', 0):.2f}")
    print(f"Win rate: {updated_performance.get('win_rate', 0):.1f}%")

    # Show updated Astra DB data
    try:
        updated_trades = trading_storage.get_recent_trades(3)
        if updated_trades:
            print(f"Recent Astra DB trades: {len(updated_trades)} found")
            if len(updated_trades) > 0:
                last_trade = updated_trades[-1]
                print(f"Last trade: {last_trade.get('symbol')} - {last_trade.get('decision')} at {last_trade.get('timestamp')}")
    except Exception as e:
        print(f"Astra DB query failed: {e}")
