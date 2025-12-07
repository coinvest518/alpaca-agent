import os
from dotenv import load_dotenv
from astrapy import DataAPIClient
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

load_dotenv()

ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")

class AstraDatabaseAgent:
    """Astra DB agent for storing and retrieving trading data."""

    def __init__(self):
        """Initialize Astra DB connection with existing collections only."""
        if not ASTRA_DB_API_ENDPOINT or not ASTRA_DB_APPLICATION_TOKEN:
            raise ValueError("Astra DB credentials not found in environment variables")

        self.client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
        self.db = self.client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)

        # List existing collections - don't create new ones
        self.existing_collections = self.db.list_collection_names()
        print(f"Found existing collections: {self.existing_collections}")

        # Use existing collections or create minimal ones if needed
        self._ensure_minimal_collections()

    def _ensure_minimal_collections(self):
        """Ensure only essential collections exist - skip performance to avoid index limits."""
        collections = self.db.list_collection_names()
        required_collections = ['trades', 'market_data', 'indicators']  # Skip 'performance'

        for collection in required_collections:
            if collection not in collections:
                try:
                    # Create collection
                    self.db.create_collection(collection)
                    print(f"Created collection: {collection}")
                except Exception as e:
                    print(f"Failed to create collection {collection}: {e}")
                    # Continue without this collection

    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data before storing."""
        masked_data = data.copy()

        # Mask API keys and tokens
        sensitive_fields = ['api_key', 'token', 'password', 'secret', 'key']
        for field in sensitive_fields:
            if field in masked_data:
                masked_data[field] = "***MASKED***"

        # Mask nested sensitive data
        for key, value in masked_data.items():
            if isinstance(value, dict):
                masked_data[key] = self._mask_sensitive_data(value)
            elif isinstance(value, list):
                masked_data[key] = [
                    self._mask_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]

        return masked_data

    # Trade Operations
    def save_trade(self, trade_data: Dict[str, Any]) -> str:
        """Save a trade record to Astra DB."""
        try:
            # Mask sensitive data before storing
            masked_trade_data = self._mask_sensitive_data(trade_data)
            
            collection = self.db.get_collection('trades')
            masked_trade_data['_id'] = f"trade_{datetime.now().isoformat()}_{masked_trade_data.get('symbol', 'unknown')}"
            result = collection.insert_one(masked_trade_data)
            return result.inserted_id
        except Exception as e:
            print(f"Error saving trade: {e}")
            return None

    def get_trades(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get trade records, optionally filtered by symbol."""
        collection = self.db.get_collection('trades')
        filter_criteria = {"symbol": symbol} if symbol else {}
        cursor = collection.find(filter_criteria).sort({"timestamp": -1}).limit(limit)
        return list(cursor)

    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get most recent trades."""
        collection = self.db.get_collection('trades')
        cursor = collection.find().sort({"timestamp": -1}).limit(limit)
        return list(cursor)

    # Market Data Operations
    def save_market_data(self, symbol: str, data: pd.DataFrame):
        """Save market data (bars) to Astra DB."""
        collection = self.db.get_collection('market_data')

        # Convert DataFrame to list of documents
        documents = []
        for timestamp, row in data.iterrows():
            doc = {
                "_id": f"bars_{symbol}_{timestamp.isoformat()}",
                "symbol": symbol,
                "timestamp": timestamp.isoformat(),
                "open": row.get('o'),
                "high": row.get('h'),
                "low": row.get('l'),
                "close": row.get('c'),
                "volume": row.get('v'),
                "vwap": row.get('vw', row.get('c'))
            }
            # Mask any sensitive data in the document
            masked_doc = self._mask_sensitive_data(doc)
            documents.append(masked_doc)

        if documents:
            try:
                # Use replace_one with upsert to handle existing documents
                for doc in documents:
                    collection.replace_one(
                        {"_id": doc["_id"]},  # Filter by ID
                        doc,                  # Replace with new document
                        upsert=True           # Insert if doesn't exist
                    )
            except Exception as e:
                print(f"Error saving market data for {symbol}: {e}")

    def get_market_data(self, symbol: str, start_date: Optional[str] = None, limit: int = 1000) -> pd.DataFrame:
        """Retrieve market data for a symbol."""
        collection = self.db.get_collection('market_data')

        filter_criteria = {"symbol": symbol}
        if start_date:
            filter_criteria["timestamp"] = {"$gte": start_date}

        cursor = collection.find(filter_criteria).sort({"timestamp": -1}).limit(limit)
        data = list(cursor)

        if not data:
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df = df.sort_index()
        return df

    # Indicator Operations
    def save_indicators(self, symbol: str, indicators: pd.DataFrame):
        """Save calculated indicators to Astra DB."""
        collection = self.db.get_collection('indicators')

        documents = []
        for timestamp, row in indicators.iterrows():
            # Convert row to dict and handle NaN values
            row_dict = row.to_dict()
            # Replace NaN values with None (which becomes null in JSON)
            cleaned_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}

            doc = {
                "_id": f"indicators_{symbol}_{timestamp.isoformat()}",
                "symbol": symbol,
                "timestamp": timestamp.isoformat(),
                **cleaned_dict
            }
            # Mask any sensitive data in the document
            masked_doc = self._mask_sensitive_data(doc)
            documents.append(masked_doc)

        if documents:
            try:
                # Use replace_one with upsert to handle existing documents
                for doc in documents:
                    collection.replace_one(
                        {"_id": doc["_id"]},  # Filter by ID
                        doc,                  # Replace with new document
                        upsert=True           # Insert if doesn't exist
                    )
            except Exception as e:
                print(f"Error saving indicators for {symbol}: {e}")

    def get_indicators(self, symbol: str, limit: int = 1000) -> pd.DataFrame:
        """Retrieve indicators for a symbol."""
        collection = self.db.get_collection('indicators')

        cursor = collection.find({"symbol": symbol}).sort({"timestamp": -1}).limit(limit)
        data = list(cursor)

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df = df.sort_index()
        return df

    # Performance Analytics
    def calculate_pnl(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Calculate profit and loss for trades."""
        trades = self.get_trades(symbol, limit=10000)

        if not trades:
            return {"total_trades": 0, "total_pnl": 0, "win_rate": 0}

        total_pnl = 0
        winning_trades = 0
        total_trades = len(trades)

        for trade in trades:
            # This is a simplified P&L calculation
            # In reality, you'd need entry/exit prices and commissions
            if trade.get('order_result') and 'filled_avg_price' in str(trade.get('order_result', {})):
                # Calculate based on order results
                pass

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        return {
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "symbol": symbol
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        all_trades = self.get_recent_trades(1000)

        if not all_trades:
            return {
                "total_trades": 0,
                "buy_decisions": 0,
                "sell_decisions": 0,
                "hold_decisions": 0,
                "pnl": 0,
                "win_rate": 0
            }

        buy_count = sum(1 for t in all_trades if t.get('decision') == 'BUY')
        sell_count = sum(1 for t in all_trades if t.get('decision') == 'SELL')
        hold_count = sum(1 for t in all_trades if t.get('decision') == 'HOLD')

        return {
            "total_trades": len(all_trades),
            "buy_decisions": buy_count,
            "sell_decisions": sell_count,
            "hold_decisions": hold_count,
            "recent_trades": all_trades[:5],
            "pnl": self.calculate_pnl()
        }

    # Backtesting Data
    def save_backtest_data(self, strategy_name: str, results: Dict[str, Any]):
        """Save backtesting results."""
        # Mask sensitive data before storing
        masked_results = self._mask_sensitive_data(results)
        
        collection = self.db.get_collection('performance')
        doc = {
            "_id": f"backtest_{strategy_name}_{datetime.now().isoformat()}",
            "strategy": strategy_name,
            "timestamp": datetime.now().isoformat(),
            **masked_results
        }
        collection.insert_one(doc)

    def get_backtest_results(self, strategy_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get backtesting results."""
        collection = self.db.get_collection('performance')

        filter_criteria = {"strategy": strategy_name} if strategy_name else {}
        cursor = collection.find(filter_criteria).sort({"timestamp": -1}).limit(limit)
        return list(cursor)

# Global instance - connect without resetting collections
# Global instance - uses existing collections only
astra_db = AstraDatabaseAgent()