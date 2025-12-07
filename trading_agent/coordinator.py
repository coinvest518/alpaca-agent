from langgraph.graph import StateGraph, END
import pandas as pd
from datetime import datetime
from typing import TypedDict, Optional, Any, Dict
import concurrent.futures
import asyncio

# Lazy imports to avoid startup issues
def _get_data_ingestor():
    from trading_agent.agents.data_ingestor import get_bars, get_account, get_positions, get_orders
    return get_bars, get_account, get_positions, get_orders

def _get_indicator_agent():
    from trading_agent.agents.indicator_agent import calculate_indicators
    return calculate_indicators

def _get_llm_agent():
    from trading_agent.agents.llm_agent import make_trade_decision
    return make_trade_decision

def _get_order_manager():
    from trading_agent.agents.order_manager import (
        place_order, place_bracket_order, place_oco_order, place_trailing_stop,
        place_limit_order, place_stop_order, place_stop_limit_order
    )
    return place_order, place_bracket_order, place_oco_order, place_trailing_stop, place_limit_order, place_stop_order, place_stop_limit_order

def _get_storage_agent():
    from trading_agent.agents.storage_agent import trading_storage
    return trading_storage

def _get_email_agent():
    from trading_agent.agents.email_agent import email_agent
    return email_agent

def _get_scraping_agent():
    from trading_agent.agents.scraping_agent import ScrapingAgent
    return ScrapingAgent()

# Define the state - simplified for account-focused trading
class TradingState(TypedDict):
    positions: Optional[Any]  # Account positions (what we actually own)
    account: Optional[Any]    # Account balance and info
    orders: Optional[Any]     # Pending orders
    analysis_results: Optional[Dict[str, Any]]  # Analysis for each position
    decisions: Optional[Dict[str, str]]  # Decisions for each position
    actions_taken: Optional[Dict[str, Any]]  # Actions executed

# Define nodes - simplified account-first approach
def get_account_positions(state):
    """Get current account positions and balance."""
    print("🔍 STEP 1: Getting account positions and balance...")
    start_time = datetime.now()

    get_bars, get_account, get_positions, get_orders = _get_data_ingestor()
    account = get_account()
    positions = get_positions()
    orders = get_orders()

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"✅ Account data retrieved in {duration:.2f}s")
    try:
        cash = float(account.get('cash', 0))
        print(f"   Cash: ${cash:.2f}")
    except (ValueError, TypeError):
        print(f"   Cash: {account.get('cash', 'Unknown')}")

    print(f"   Positions: {len(positions) if positions else 0} stocks")
    print(f"   Orders: {len(orders) if orders else 0} pending orders")

    state['account'] = account
    state['positions'] = positions
    state['orders'] = orders
    return state

def analyze_single_position(position):
    """Analyze a single position - helper for parallel processing."""
    symbol = position.get('symbol')
    if not symbol:
        return None
    
    # Get recent market data for this position (last 24 hours, 5-min bars)
    get_bars_func, _, _, _ = _get_data_ingestor()
    bars = get_bars_func(symbol, timeframe="5Min", hours_back=24)
    if bars is None:
        return None
    
    # Calculate indicators
    calculate_indicators_func = _get_indicator_agent()
    indicators = calculate_indicators_func(bars)
    
    # Get historical trades for this symbol
    trading_storage_func = _get_storage_agent()
    historical_trades = trading_storage_func.get_trades_for_symbol(symbol)
    
    # Gather news and market intelligence
    news_data = None
    market_intelligence = None
    try:
        scraper = _get_scraping_agent()
        print(f"📰 Gathering news for {symbol}...")
        news_data = scraper.scrape_financial_news(symbol)
        
        # Also scrape broader market data (e.g., market overview)
        print(f"📊 Gathering market intelligence...")
        market_intelligence = scraper.scrape_market_data("https://finance.yahoo.com/")
        
    except Exception as e:
        print(f"⚠️  News gathering failed for {symbol}: {e}")
    
    # Save market data and indicators
    trading_storage_func.save_market_data(symbol, bars)
    trading_storage_func.save_indicators(symbol, indicators)
    
    return {
        'symbol': symbol,
        'position': position,
        'bars': bars,
        'indicators': indicators,
        'historical_trades': historical_trades,
        'news': news_data,
        'market_intelligence': market_intelligence
    }

def analyze_positions(state):
    """Analyze each position in the account."""
    print("\n📊 STEP 2: Analyzing positions...")
    start_time = datetime.now()

    if not state['positions']:
        print("⚠️  No positions found to analyze")
        state['analysis_results'] = {}
        return state

    analysis_results = {}
    total_positions = len(state['positions'])

    print(f"🔄 Analyzing {total_positions} positions in parallel...")

    # Use ThreadPoolExecutor for parallel analysis
    analysis_results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(total_positions, 5)) as executor:
        # Submit all analysis tasks
        future_to_position = {
            executor.submit(analyze_single_position, position): position 
            for position in state['positions']
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_position):
            result = future.result()
            if result:
                symbol = result['symbol']
                analysis_results[symbol] = result
                print(f"✅ {symbol}: Analysis complete")

    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()

    print(f"✅ Position analysis complete in {total_duration:.2f}s")
    print(f"   Successfully analyzed: {len(analysis_results)}/{total_positions} positions")

    state['analysis_results'] = analysis_results
    return state

def make_single_decision(symbol, analysis, account):
    """Make decision for a single position - helper for parallel processing."""
    position = analysis['position']
    
    # Get position details (convert strings to floats)
    try:
        current_price = float(position.get('current_price', 0))
        avg_entry_price = float(position.get('avg_entry_price', 0))
        qty = int(float(position.get('qty', 0)))
        unrealized_pl = float(position.get('unrealized_pl', 0))
        unrealized_plpc = float(position.get('unrealized_plpc', 0))
    except (ValueError, TypeError):
        current_price = 0.0
        avg_entry_price = 0.0
        qty = 0
        unrealized_pl = 0.0
        unrealized_plpc = 0.0

    # Get indicators
    indicators = analysis['indicators']
    if indicators is not None and not indicators.empty:
        latest_indicators = indicators.tail(1).to_dict('records')[0]
    else:
        latest_indicators = {}

    # Make decision using LLM with position context
    make_trade_decision_func = _get_llm_agent()
    decision = make_trade_decision_func(
        symbol=symbol,
        position_data=position,
        indicators=latest_indicators,
        account_data=account,
        historical_trades=analysis['historical_trades'],
        news_data=analysis.get('news'),
        market_intelligence=analysis.get('market_intelligence')
    )

    return {
        'symbol': symbol,
        'decision': decision,
        'position': position,
        'indicators': latest_indicators
    }

def make_position_decisions(state):
    """Make decisions for each analyzed position."""
    print("\n🧠 STEP 3: Making trading decisions...")
    start_time = datetime.now()

    if not state['analysis_results']:
        print("⚠️  No analysis results to make decisions on")
        state['decisions'] = {}
        return state

    decisions = {}
    total_symbols = len(state['analysis_results'])

    print(f"🤖 Getting AI decisions for {total_symbols} positions in parallel...")

    # Use ThreadPoolExecutor for parallel decision making
    decisions = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(total_symbols, 5)) as executor:
        # Submit all decision tasks
        future_to_symbol = {
            executor.submit(make_single_decision, symbol, analysis, state['account']): symbol 
            for symbol, analysis in state['analysis_results'].items()
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_symbol):
            result = future.result()
            symbol = result['symbol']
            decisions[symbol] = {
                'decision': result['decision'],
                'position': result['position'],
                'indicators': result['indicators']
            }
            print(f"✅ {symbol}: Decision '{result['decision']}' complete")

    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()

    print(f"✅ Decision making complete in {total_duration:.2f}s")
    print(f"   Decisions made: {len(decisions)}/{total_symbols}")

    state['decisions'] = decisions
    return state

def execute_actions(state):
    """Execute the decided actions."""
    print("\n⚡ STEP 4: Executing trading actions...")
    start_time = datetime.now()

    if not state['decisions']:
        print("⚠️  No decisions to execute")
        state['actions_taken'] = {}
        return state

    actions_taken = {}
    total_decisions = len(state['decisions'])

    print(f"🔄 Processing {total_decisions} decisions...")

    for symbol, decision_data in state['decisions'].items():
        decision = decision_data['decision']
        position = decision_data['position']

        print(f"📋 {symbol}: Processing decision '{decision}'...")

        if decision == "BRACKET_BUY":
            # Smart bracket buy: entry + take-profit + stop-loss
            cash = float(state['account'].get('cash', 0))
            current_price = float(position.get('current_price', 0))
            
            # Calculate smart prices based on technicals
            entry_price = current_price * 0.995  # Buy at 0.5% discount
            take_profit_price = current_price * 1.05  # 5% profit target
            stop_loss_price = current_price * 0.97  # 3% stop loss
            
            if cash > entry_price * 2:  # Can afford at least 2 shares
                shares_to_buy = min(10, int(cash // entry_price))  # Buy up to 10 shares
                print(f"   🎯 Smart Bracket Buy: {shares_to_buy} shares")
                print(f"      Entry: ${entry_price:.2f}, Target: ${take_profit_price:.2f}, Stop: ${stop_loss_price:.2f}")
                
                order = _get_order_manager().place_bracket_order(symbol, shares_to_buy, "buy", entry_price, take_profit_price, stop_loss_price)
                actions_taken[symbol] = {"action": "BRACKET_BUY", "shares": shares_to_buy, "order": order}
                print(f"   ✅ Bracket order placed: {shares_to_buy} shares with profit protection")
            else:
                actions_taken[symbol] = {"action": "HOLD", "reason": "Insufficient cash for bracket buy"}
                print(f"   ❌ Insufficient cash for smart bracket buy")

        elif decision == "LIMIT_BUY":
            # Buy at better price than market
            cash = float(state['account'].get('cash', 0))
            current_price = float(position.get('current_price', 0))
            
            limit_price = current_price * 0.98  # Buy at 2% discount
            if cash > limit_price * 2:
                shares_to_buy = min(5, int(cash // limit_price))
                print(f"   🎯 Limit Buy: {shares_to_buy} shares at ${limit_price:.2f}")
                
                order = _get_order_manager().place_limit_order(symbol, shares_to_buy, "buy", limit_price)
                actions_taken[symbol] = {"action": "LIMIT_BUY", "shares": shares_to_buy, "limit_price": limit_price, "order": order}
                print(f"   ✅ Limit buy order placed: {shares_to_buy} shares")
            else:
                actions_taken[symbol] = {"action": "HOLD", "reason": "Cash insufficient for limit buy"}
                print(f"   ❌ Insufficient cash for limit buy")

        elif decision == "TRAILING_STOP_BUY":
            # Set trailing stop for long position
            qty = int(float(position.get('qty', 0)))
            current_price = float(position.get('current_price', 0))
            
            if qty > 0:
                trail_percent = 2.0  # 2% trailing stop
                print(f"   🎯 Trailing Stop Buy: Protect {qty} shares with {trail_percent}% trail")
                
                order = _get_order_manager().place_trailing_stop(symbol, qty, "sell", trail_percent=trail_percent)
                actions_taken[symbol] = {"action": "TRAILING_STOP_BUY", "shares": qty, "trail_percent": trail_percent, "order": order}
                print(f"   ✅ Trailing stop set for {qty} shares")
            else:
                actions_taken[symbol] = {"action": "HOLD", "reason": "No position to protect"}
                print(f"   ❌ No position to set trailing stop")

        elif decision == "OCO_SELL":
            # Smart OCO sell: take-profit + stop-loss
            qty = int(float(position.get('qty', 0)))
            current_price = float(position.get('current_price', 0))
            
            if qty > 0:
                # Smart profit targets based on current P&L
                unrealized_plpc = float(position.get('unrealized_plpc', 0))
                
                if unrealized_plpc > 5:  # Good profit, take more
                    take_profit_price = current_price * 1.02  # 2% more profit
                    stop_loss_price = current_price * 0.98  # Protect 2% below current
                elif unrealized_plpc > 2:  # Decent profit
                    take_profit_price = current_price * 1.03  # 3% more profit  
                    stop_loss_price = current_price * 0.97  # Protect 3% below current
                else:  # Small profit or loss
                    take_profit_price = current_price * 1.05  # 5% profit target
                    stop_loss_price = current_price * 0.95  # 5% stop loss
                
                print(f"   🎯 Smart OCO Sell: {qty} shares")
                print(f"      Take Profit: ${take_profit_price:.2f}, Stop Loss: ${stop_loss_price:.2f}")
                
                order = _get_order_manager().place_oco_order(symbol, qty, take_profit_price, stop_loss_price)
                actions_taken[symbol] = {"action": "OCO_SELL", "shares": qty, "take_profit": take_profit_price, "stop_loss": stop_loss_price, "order": order}
                print(f"   ✅ OCO order placed: take-profit + stop-loss protection")
            else:
                actions_taken[symbol] = {"action": "HOLD", "reason": "No position to sell"}
                print(f"   ❌ No position to place OCO order")

        elif decision == "LIMIT_SELL":
            # Sell at better price than market
            qty = int(float(position.get('qty', 0)))
            current_price = float(position.get('current_price', 0))
            
            if qty > 0:
                limit_price = current_price * 1.02  # Sell at 2% premium
                print(f"   🎯 Limit Sell: {qty} shares at ${limit_price:.2f}")
                
                order = _get_order_manager().place_limit_order(symbol, qty, "sell", limit_price)
                actions_taken[symbol] = {"action": "LIMIT_SELL", "shares": qty, "limit_price": limit_price, "order": order}
                print(f"   ✅ Limit sell order placed: {qty} shares")
            else:
                actions_taken[symbol] = {"action": "HOLD", "reason": "No position to sell"}
                print(f"   ❌ No position to sell")

        elif decision == "TRAILING_STOP_SELL":
            # Set trailing stop to let profits run
            qty = int(float(position.get('qty', 0)))
            current_price = float(position.get('current_price', 0))
            
            if qty > 0:
                trail_percent = 3.0  # 3% trailing stop for profit protection
                print(f"   🎯 Trailing Stop Sell: Let profits run on {qty} shares with {trail_percent}% trail")
                
                order = _get_order_manager().place_trailing_stop(symbol, qty, "sell", trail_percent=trail_percent)
                actions_taken[symbol] = {"action": "TRAILING_STOP_SELL", "shares": qty, "trail_percent": trail_percent, "order": order}
                print(f"   ✅ Trailing stop set for profit protection")
            else:
                actions_taken[symbol] = {"action": "HOLD", "reason": "No position to protect"}
                print(f"   ❌ No position to set trailing stop")

        elif decision == "STOP_LOSS":
            # Add stop-loss protection
            qty = int(float(position.get('qty', 0)))
            current_price = float(position.get('current_price', 0))
            
            if qty > 0:
                stop_price = current_price * 0.95  # 5% stop loss
                print(f"   🛡️ Stop Loss: Protect {qty} shares below ${stop_price:.2f}")
                
                order = _get_order_manager().place_stop_order(symbol, qty, "sell", stop_price)
                actions_taken[symbol] = {"action": "STOP_LOSS", "shares": qty, "stop_price": stop_price, "order": order}
                print(f"   ✅ Stop-loss order placed for risk protection")
            else:
                actions_taken[symbol] = {"action": "HOLD", "reason": "No position to protect"}
                print(f"   ❌ No position to add stop-loss")

        elif decision == "REDUCE_POSITION":
            # Sell partial position to lock in profits
            qty = int(float(position.get('qty', 0)))
            current_price = float(position.get('current_price', 0))
            
            if qty > 1:
                shares_to_sell = qty // 2  # Sell half
                print(f"   💰 Reduce Position: Sell {shares_to_sell} of {qty} shares")
                
                order = _get_order_manager().place_order(symbol, shares_to_sell, "sell")  # Market order for quick execution
                actions_taken[symbol] = {"action": "REDUCE_POSITION", "shares": shares_to_sell, "order": order}
                print(f"   ✅ Sold {shares_to_sell} shares to lock in profits")
            else:
                actions_taken[symbol] = {"action": "HOLD", "reason": "Position too small to reduce"}
                print(f"   ❌ Position too small to reduce")

        elif decision == "BUY_MORE":
            # Legacy support - map to BRACKET_BUY
            cash = float(state['account'].get('cash', 0))
            current_price = float(position.get('current_price', 0))
            print(f"   💰 Cash: ${cash:.2f}, Stock Price: ${current_price:.2f}")

            if cash > current_price * 2:  # Can afford at least 2 shares
                shares_to_buy = min(5, int(cash // current_price))  # Buy up to 5 shares
                print(f"   🛒 Buying {shares_to_buy} shares of {symbol}...")
                order = _get_order_manager().place_order(symbol, shares_to_buy, "buy")
                actions_taken[symbol] = {"action": "BUY_MORE", "shares": shares_to_buy, "order": order}
                print(f"   ✅ Buy order placed: {shares_to_buy} shares")
            else:
                actions_taken[symbol] = {"action": "HOLD", "reason": "Insufficient cash"}
                print(f"   ❌ Insufficient cash to buy more {symbol}")

        elif decision == "SELL_PARTIAL":
            # Legacy support - map to REDUCE_POSITION
            qty = int(float(position.get('qty', 0)))
            print(f"   📊 Current position: {qty} shares")

            if qty > 1:
                shares_to_sell = qty // 2
                print(f"   💸 Selling {shares_to_sell} shares of {symbol}...")
                order = _get_order_manager().place_order(symbol, shares_to_sell, "sell")
                actions_taken[symbol] = {"action": "SELL_PARTIAL", "shares": shares_to_sell, "order": order}
                print(f"   ✅ Sell order placed: {shares_to_sell} shares")
            else:
                actions_taken[symbol] = {"action": "HOLD", "reason": "Position too small to sell partial"}
                print(f"   ❌ Position too small to sell partial")

        elif decision == "SELL_ALL":
            # Legacy support - map to OCO_SELL
            qty = int(float(position.get('qty', 0)))
            print(f"   📊 Current position: {qty} shares")

            if qty > 0:
                print(f"   💸 Selling all {qty} shares of {symbol}...")
                order = _get_order_manager().place_order(symbol, qty, "sell")
                actions_taken[symbol] = {"action": "SELL_ALL", "shares": qty, "order": order}
                print(f"   ✅ Sell order placed: {qty} shares")
            else:
                actions_taken[symbol] = {"action": "HOLD", "reason": "No position to sell"}
                print(f"   ❌ No position to sell")

        else:  # HOLD
            actions_taken[symbol] = {"action": "HOLD", "reason": "No action needed"}
            print(f"   ⏸️  Holding {symbol} position")

    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()

    print(f"✅ Action execution complete in {total_duration:.2f}s")
    print(f"   Actions taken: {len([a for a in actions_taken.values() if a['action'] != 'HOLD'])} trades")

    state['actions_taken'] = actions_taken
    return state

def log_actions(state):
    """Log all actions taken and send email report."""
    print("\n📝 STEP 5: Logging and sending report...")
    start_time = datetime.now()

    # Collect comprehensive trading data for email
    trading_data = {
        'cycle_duration': getattr(state, 'cycle_duration', None),
        'account': state.get('account', {}),
        'positions': state.get('positions', []),
        'orders': state.get('orders', []),
        'analysis_results': state.get('analysis_results', {}),
        'decisions': state.get('decisions', {}),
        'actions_taken': state.get('actions_taken', {}),
        'news_data': {},  # Will be populated if news agent exists
        'technical_analysis': {},
        'ai_reasoning': {},
        'total_trades': 0,
        'total_pnl': '0.00',
        'win_rate': '0.0'
    }

    # Extract technical analysis data
    for symbol, analysis in state.get('analysis_results', {}).items():
        if analysis.get('indicators') is not None and not analysis['indicators'].empty:
            trading_data['technical_analysis'][symbol] = analysis['indicators'].tail(1).to_dict('records')[0]

    # Extract news and market intelligence data
    for symbol, analysis in state.get('analysis_results', {}).items():
        if analysis.get('news'):
            trading_data['news_data'][symbol] = analysis['news']
            print(f"📰 News data for {symbol}: {len(analysis['news']) if isinstance(analysis['news'], list) else 'Not a list'} items")
        else:
            print(f"📰 No news data found for {symbol}")
            
        if analysis.get('market_intelligence'):
            trading_data['market_intelligence'] = analysis['market_intelligence']
            print(f"🌍 Market intelligence data: {type(analysis['market_intelligence'])}")

    # Extract AI reasoning from decisions
    for symbol, decision_data in state.get('decisions', {}).items():
        decision = decision_data.get('decision', '')
        position = decision_data.get('position', {})
        indicators = decision_data.get('indicators', {})

        reasoning = f"Decision: {decision}\n"
        try:
            current_price = float(position.get('current_price', 0))
            reasoning += f"Current Price: ${current_price:.2f}\n"
        except (ValueError, TypeError):
            reasoning += f"Current Price: {position.get('current_price', 'N/A')}\n"
        
        try:
            unrealized_plpc = float(position.get('unrealized_plpc', 0))
            reasoning += f"Unrealized P&L: {unrealized_plpc:.2f}%\n"
        except (ValueError, TypeError):
            reasoning += f"Unrealized P&L: {position.get('unrealized_plpc', 'N/A')}%\n"
        
        if indicators:
            indicator_strs = []
            for k, v in indicators.items():
                try:
                    if isinstance(v, (int, float)):
                        indicator_strs.append(f"{k}: {v:.2f}")
                    else:
                        indicator_strs.append(f"{k}: {v}")
                except:
                    indicator_strs.append(f"{k}: {v}")
            reasoning += f"Key Indicators: {', '.join(indicator_strs)}"

        trading_data['ai_reasoning'][symbol] = reasoning

    # Get performance metrics
    try:
        performance = _get_storage_agent().get_performance_summary()
        trading_data.update({
            'total_trades': performance.get('total_trades', 0),
            'total_pnl': f"{performance.get('total_pnl', 0):.2f}",
            'win_rate': f"{performance.get('win_rate', 0):.1f}"
        })
    except:
        pass

    if state['actions_taken']:
        print("💾 Saving trade records to database...")
        saved_count = 0

        for symbol, action in state['actions_taken'].items():
            print(f"📊 {symbol}: {action}")

            # Save trade record if order was placed
            if 'order' in action and action['order']:
                _get_storage_agent().add_trade_record(
                    symbol=symbol,
                    decision=action['action'],
                    indicators=state['decisions'][symbol]['indicators'],
                    account=state['account'] or {},
                    order_result=action['order']
                )
                saved_count += 1

        print(f"✅ Saved {saved_count} trade records to Astra DB")
    else:
        print("ℹ️  No actions to log")

    # Send email report
    print("📧 Sending trading report email...")
    email_sent = _get_email_agent().send_trading_report(trading_data)
    if email_sent:
        print("✅ Email report sent successfully!")
    else:
        print("❌ Failed to send email report")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"✅ Logging and reporting complete in {duration:.2f}s")

    return state

# Create the simplified graph
graph = StateGraph(TradingState)
graph.add_node("get_account_positions", get_account_positions)
graph.add_node("analyze_positions", analyze_positions)
graph.add_node("make_position_decisions", make_position_decisions)
graph.add_node("execute_actions", execute_actions)
graph.add_node("log_actions", log_actions)

graph.set_entry_point("get_account_positions")
graph.add_edge("get_account_positions", "analyze_positions")
graph.add_edge("analyze_positions", "make_position_decisions")
graph.add_edge("make_position_decisions", "execute_actions")
graph.add_edge("execute_actions", "log_actions")
graph.add_edge("log_actions", END)

# Compile the graph
app = graph.compile()

def run_trading_cycle():
    """Run one complete trading cycle for all account positions."""
    print("🚀 STARTING TRADING CYCLE")
    cycle_start = datetime.now()

    initial_state = {
        'positions': None,
        'account': None,
        'orders': None,
        'analysis_results': None,
        'decisions': None,
        'actions_taken': None
    }

    result = app.invoke(initial_state)

    cycle_end = datetime.now()
    total_duration = (cycle_end - cycle_start).total_seconds()

    # Add cycle duration to result for email reporting
    result['cycle_duration'] = f"{total_duration:.2f}"

    print(f"\n🎯 TRADING CYCLE COMPLETE - Total time: {total_duration:.2f}s")
    print("=" * 60)

    return result