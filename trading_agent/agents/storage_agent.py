import os
from datetime import datetime
from typing import Dict, List, Any
from .astra_db_agent import astra_db

class TradingStorage:
    """Storage system for trading history and AI memory using Astra DB."""

    def __init__(self):
        # Simplified storage without langchain dependencies for now
        pass

    def add_trade_record(self, symbol: str, decision: str, indicators: Dict, account: Dict, order_result: Dict = None):
        """Add a trade record to Astra DB."""
        trade_data = {
            "timestamp": datetime.now(),
            "symbol": symbol,
            "decision": decision,
            "indicators": indicators,
            "account_balance": account.get('cash', 0),
            "buying_power": account.get('buying_power', 0),
            "order_result": order_result
        }

        # Save to Astra DB
        astra_db.save_trade(trade_data)

        # Add to AI memory
        memory_text = f"Trade Decision for {symbol}: {decision} | Account: ${account.get('cash', 0)} | Indicators: {indicators}"
        self.memory.save_context({"input": f"Analyzed {symbol}"}, {"output": memory_text})

    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trading records from Astra DB."""
        return astra_db.get_recent_trades(limit)

    def get_trades_for_symbol(self, symbol: str) -> List[Dict]:
        """Get trading history for a specific symbol from Astra DB."""
        return astra_db.get_trades(symbol, limit=50)  # Last 50 trades for this symbol

    def get_memory_context(self) -> str:
        """Get AI memory context for decision making."""
        if self.memory.buffer:
            return str(self.memory.buffer[-5:])  # Last 5 memories
        return "No previous trading context available."

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from Astra DB."""
        return astra_db.get_performance_summary()

    # Additional Astra DB methods
    def save_market_data(self, symbol: str, data):
        """Save market data to Astra DB."""
        astra_db.save_market_data(symbol, data)

    def get_market_data(self, symbol: str, start_date=None, limit=1000):
        """Get market data from Astra DB."""
        return astra_db.get_market_data(symbol, start_date, limit)

    def save_indicators(self, symbol: str, indicators):
        """Save indicators to Astra DB."""
        astra_db.save_indicators(symbol, indicators)

    def get_indicators(self, symbol: str, limit=1000):
        """Get indicators from Astra DB."""
        return astra_db.get_indicators(symbol, limit)

    def calculate_pnl(self, symbol=None):
        """Calculate P&L from Astra DB."""
        return astra_db.calculate_pnl(symbol)

# Global storage instance
trading_storage = TradingStorage()