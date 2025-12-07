import os
import pandas as pd
from langchain_google_genai import GoogleGenerativeAI
from langsmith import traceable
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"

if LANGSMITH_TRACING:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

llm = GoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)

@traceable
def format_prompt(subject, data):
    """Format the prompt for the LLM."""
    account_info = """
    ACCOUNT CAPABILITIES:
    - Commission-Free Trading: $0 commissions on US stocks/ETFs and options
    - Available Assets: Only US stocks and ETFs (forex is blocked)
    - API Limits: 200 calls/minute
    - Order Types: Market, Limit, Stop, MOO/LOO, MOC/LOC, IOC
    - Account Balance: ~$12 cash available
    - Trading Hours: Regular and extended hours
    
    RISK MANAGEMENT:
    - Only trade with available cash
    - Consider position sizing (max 10-20% of portfolio per trade)
    - Use stop losses to limit losses
    - Avoid overtrading due to API limits
    
    DECISION CRITERIA:
    - Use technical indicators (EMA, RSI, ATR, volatility) for signals
    - BUY when: Strong uptrend + oversold RSI + low volatility
    - SELL when: Strong downtrend + overbought RSI + high volatility  
    - HOLD when: Mixed signals or high uncertainty
    """
    
    prompt = f"""{account_info}
    
    Based on the technical indicators below, decide to BUY, SELL, or HOLD for {subject}.
    Only recommend trades that fit within account capabilities and risk limits.
    
    Technical Data (last 10 periods):
    {data}
    
    Respond with only: BUY, SELL, or HOLD"""
    return prompt

@traceable(run_type="llm")
def invoke_llm(messages):
    """Invoke the LLM with the messages."""
    response = llm.invoke(messages)
    return response

@traceable
def parse_output(response):
    """Parse the LLM output to extract the decision."""
    # Handle both string responses and objects with content attribute
    if hasattr(response, 'content'):
        text = response.content.strip().upper()
    else:
        text = str(response).strip().upper()
    
    # Map to new profit-focused decisions
    if "BRACKET_BUY" in text:
        return "BRACKET_BUY"
    elif "LIMIT_BUY" in text:
        return "LIMIT_BUY"
    elif "TRAILING_STOP_BUY" in text:
        return "TRAILING_STOP_BUY"
    elif "OCO_SELL" in text:
        return "OCO_SELL"
    elif "LIMIT_SELL" in text:
        return "LIMIT_SELL"
    elif "TRAILING_STOP_SELL" in text:
        return "TRAILING_STOP_SELL"
    elif "STOP_LOSS" in text:
        return "STOP_LOSS"
    elif "REDUCE_POSITION" in text:
        return "REDUCE_POSITION"
    elif "BUY_MORE" in text:
        return "BRACKET_BUY"  # Map old decisions to new ones
    elif "SELL_PARTIAL" in text:
        return "OCO_SELL"
    elif "SELL_ALL" in text:
        return "OCO_SELL"
    else:
        return "HOLD"

@traceable
def run_pipeline(symbol, data):
    """Run the full pipeline for trade decision."""
    prompt = format_prompt(symbol, data)
    response = invoke_llm(prompt)
    decision = parse_output(response)
    return decision

@traceable
def _explain_indicator_simple(indicator, value):
    """Explain technical indicators in simple terms for beginners."""
    try:
        if indicator.lower() == 'rsi':
            rsi_val = float(value)
            if rsi_val < 30:
                return "Stock is cheap (oversold) - might be a good BUY signal"
            elif rsi_val > 70:
                return "Stock is expensive (overbought) - might be a good SELL signal"
            else:
                return "Stock is fairly priced (normal range)"
        elif indicator.lower() == 'ema':
            return "Average price over time (smoother than daily prices)"
        elif indicator.lower() == 'atr':
            atr_val = float(value)
            if atr_val < 0.5:
                return "Price doesn't move much (stable)"
            elif atr_val < 2.0:
                return "Normal price movement"
            else:
                return "Price moves a lot (volatile)"
        elif indicator.lower() == 'volatility_score':
            vol_val = float(value)
            if vol_val < 2:
                return "Low risk - price is stable"
            elif vol_val < 5:
                return "Medium risk - normal swings"
            else:
                return "High risk - big price swings"
        else:
            return f"Technical indicator measuring {indicator}"
    except:
        return f"Technical indicator: {indicator}"

def make_trade_decision(symbol, position_data=None, indicators=None, account_data=None, historical_trades=None, news_data=None, market_intelligence=None):
    """Make a smart, fast profit-based trade decision using advanced order types."""
    data_str = f"🚀 PROFIT ANALYSIS for {symbol}:\n"

    # Add position details with profit/loss focus
    if position_data:
        qty = float(position_data.get('qty', 0))
        avg_entry_price = float(position_data.get('avg_entry_price', 0))
        current_price = float(position_data.get('current_price', 0))
        unrealized_pl = float(position_data.get('unrealized_pl', 0))
        unrealized_plpc = float(position_data.get('unrealized_plpc', 0))

        # Calculate profit potential
        profit_potential = (current_price - avg_entry_price) / avg_entry_price * 100
        
        data_str += f"""
        📊 POSITION: {qty} shares
        💰 Entry: ${avg_entry_price:.2f} | Current: ${current_price:.2f}
        📈 P&L: ${unrealized_pl:.2f} ({unrealized_plpc:.1f}%)
        🎯 Profit Potential: {profit_potential:.1f}%
        """

    # Add technical indicators for smart decisions
    if indicators:
        data_str += f"\n📈 TECHNICAL SIGNALS:\n"
        for key, value in indicators.items():
            if pd.notna(value):
                explanation = _explain_indicator_simple(key, value)
                if key == 'rsi':
                    signal = "🟢 OVERSOLD (<30)" if value < 30 else "🔴 OVERBOUGHT (>70)" if value > 70 else "🟡 NEUTRAL"
                    data_str += f"RSI: {value:.1f} {signal} - {explanation}\n"
                elif key == 'ema':
                    data_str += f"EMA: ${value:.2f} - {explanation}\n"
                elif key == 'atr':
                    data_str += f"ATR (Volatility): ${value:.2f} - {explanation}\n"
                elif key == 'volatility_score':
                    risk = "🟢 LOW RISK" if value < 2 else "🟡 MEDIUM RISK" if value < 5 else "🔴 HIGH RISK"
                    data_str += f"Volatility: {value:.1f}% {risk} - {explanation}\n"

    # Add account info for smart sizing
    if account_data:
        try:
            cash = float(account_data.get('cash', 0))
            buying_power = float(account_data.get('buying_power', 0))
        except (ValueError, TypeError):
            cash = 0.0
            buying_power = 0.0

        data_str += f"""
        💵 Cash: ${cash:.2f}
        ⚡ Buying Power: ${buying_power:.2f}
        """

    # Add recent performance for learning
    if historical_trades and len(historical_trades) > 0:
        recent_trades = historical_trades[-3:]
        win_rate = sum(1 for t in recent_trades if t.get('decision') in ['SELL_PARTIAL', 'SELL_ALL']) / len(recent_trades) * 100
        data_str += f"\n📊 RECENT PERFORMANCE: {win_rate:.0f}% Success Rate\n"

    # Add news and market intelligence
    if news_data:
        data_str += f"\n📰 LATEST NEWS:\n"
        if isinstance(news_data, list) and len(news_data) > 0:
            for i, news_item in enumerate(news_data[:3]):  # Show top 3 news items
                title = news_item.get('title', 'No title')
                summary = news_item.get('summary', 'No summary')
                sentiment = news_item.get('sentiment', 'neutral')
                data_str += f"{i+1}. {title[:100]}... ({sentiment})\n"
        else:
            data_str += f"No recent news available\n"

    if market_intelligence:
        data_str += f"\n🌍 MARKET INTELLIGENCE:\n"
        if isinstance(market_intelligence, dict):
            # Extract key market indicators
            market_summary = market_intelligence.get('summary', 'No market summary available')
            market_sentiment = market_intelligence.get('sentiment', 'neutral')
            key_levels = market_intelligence.get('key_levels', [])
            
            data_str += f"Market Sentiment: {market_sentiment}\n"
            data_str += f"Summary: {market_summary[:200]}...\n"
            
            if key_levels:
                data_str += f"Key Levels: {', '.join(key_levels[:3])}\n"
        else:
            data_str += f"No market intelligence available\n"

    # Create FAST, SMART decision prompt
    prompt = f"""{data_str}

    ⚡ MAKE FAST PROFIT DECISION - Choose ONE action:

    🎯 PROFIT MAXIMIZATION OPTIONS:
    BRACKET_BUY - Buy more shares with automatic profit-taking + stop-loss protection
    LIMIT_BUY - Buy at better price than current market
    TRAILING_STOP_BUY - Set trailing stop for long position to let profits run
    
    💰 PROFIT TAKING OPTIONS:  
    OCO_SELL - Place take-profit + stop-loss for current position (smart exit)
    LIMIT_SELL - Sell at higher price than current market
    TRAILING_STOP_SELL - Set trailing stop to protect profits while letting winners run
    
    🛡️ RISK MANAGEMENT:
    STOP_LOSS - Add stop-loss protection to prevent losses
    REDUCE_POSITION - Sell partial position to lock in some profits
    
    ⏸️ HOLD - Wait for better opportunity

    🎪 CRITICAL RULES:
    - If >5% profit: TAKE PROFITS with OCO_SELL or TRAILING_STOP_SELL
    - If <2% profit: ADD to position with BRACKET_BUY if cash available  
    - If RSI <30: BUY OPPORTUNITY (oversold)
    - If RSI >70: SELL OPPORTUNITY (overbought)
    - If high volatility: Use LIMIT orders, avoid MARKET orders
    - Always protect profits with stop-losses
    - Consider NEWS sentiment: Positive news + technical signals = BUY opportunity
    - Consider MARKET sentiment: Bullish market + positive news = stronger BUY signal
    - Negative news + technical weakness = SELL signal
    - Use news to confirm or contradict technical signals

    Respond with ONLY: BRACKET_BUY, LIMIT_BUY, TRAILING_STOP_BUY, OCO_SELL, LIMIT_SELL, TRAILING_STOP_SELL, STOP_LOSS, REDUCE_POSITION, or HOLD"""

    decision = run_pipeline(symbol, prompt)
    return decision