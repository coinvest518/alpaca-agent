import os
from composio import Composio
from datetime import datetime

class EmailAgent:
    """Agent for sending trading reports via Outlook email using Composio."""

    def __init__(self):
        api_key = os.getenv("COMPOSIO_API_KEY")
        if api_key:
            self.composio = Composio(api_key=api_key)
            self.connected_account_id = "ca_OLIVsrYv6cHd"  # Outlook connected account
            self.user_id = "pg-test-f7631f58-67ef-454c-bb39-984b3f271f2b"  # Entity ID from connected account
            self.enabled = True
        else:
            self.composio = None
            self.enabled = False
            print("⚠️  Email agent disabled - COMPOSIO_API_KEY not found")

    def send_trading_report(self, trading_data):
        """Send a comprehensive trading report email."""
        if not self.enabled:
            print("⚠️  Email sending skipped - agent not enabled")
            return

        # Format the email content
        subject = f"🤖 AI Trading Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        body = self._format_email_body(trading_data)

        # Save email to file as backup
        self._save_email_to_file(subject, body)

        try:
            # Send email using Composio SDK with new API
            result = self.composio.tools.execute(
                slug="OUTLOOK_SEND_EMAIL",
                arguments={
                    "to_email": "coinvest518@gmail.com",
                    "subject": subject,
                    "body": body,
                    "is_html": True,
                    "save_to_sent_items": True
                },
                connected_account_id=self.connected_account_id,
                version="20251202_01",
                user_id=self.user_id
            )

            if result.get("successful", False):
                print("✅ Trading report email sent successfully!")
                return True
            else:
                print(f"❌ Failed to send email: {result.get('error', 'Unknown error')}")
                print("📄 Email content saved to email_backup.html for review")
                return False

        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            print("📄 Email content saved to email_backup.html for review")
            return False

    def _save_email_to_file(self, subject, body):
        """Save email content to a file for review."""
        try:
            with open("email_backup.html", "w", encoding="utf-8") as f:
                f.write(f"<!-- Subject: {subject} -->\n")
                f.write(body)
            print("💾 Email content saved to email_backup.html")
        except Exception as e:
            print(f"❌ Failed to save email backup: {str(e)}")

    def _format_email_body(self, data):
        """Format trading data into HTML email body."""

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Trading Report</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: #f8f9fa;
                    padding: 20px;
                }}
                .container {{
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 300;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                    font-size: 16px;
                }}
                .section {{
                    padding: 30px;
                    border-bottom: 1px solid #eee;
                }}
                .section:last-child {{
                    border-bottom: none;
                }}
                .section h2 {{
                    color: #2c3e50;
                    font-size: 22px;
                    margin-bottom: 20px;
                    display: flex;
                    align-items: center;
                }}
                .section h2:before {{
                    content: '📊';
                    margin-right: 10px;
                }}
                .metrics {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                .metric {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    border: 1px solid #e9ecef;
                }}
                .metric-value {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #495057;
                    display: block;
                    margin-bottom: 5px;
                }}
                .metric-label {{
                    color: #6c757d;
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .decision {{
                    background: #e8f8f5;
                    border-left: 4px solid #20c997;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 0 8px 8px 0;
                }}
                .hold {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 0 8px 8px 0;
                }}
                .sell {{
                    background: #f8d7da;
                    border-left: 4px solid #dc3545;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 0 8px 8px 0;
                }}
                .buy {{
                    background: #d1ecf1;
                    border-left: 4px solid #17a2b8;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 0 8px 8px 0;
                }}
                .position-details {{
                    font-size: 14px;
                    color: #6c757d;
                    margin-top: 8px;
                }}
                .ai-reasoning {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 15px 0;
                    border: 1px solid #e9ecef;
                }}
                .ai-reasoning h3 {{
                    margin-top: 0;
                    color: #495057;
                    font-size: 18px;
                }}
                .footer {{
                    background: #343a40;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    font-size: 14px;
                }}
                .status-indicator {{
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    margin-right: 8px;
                }}
                .status-active {{
                    background: #28a745;
                }}
                .status-inactive {{
                    background: #6c757d;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f8f9fa;
                    font-weight: 600;
                    color: #495057;
                }}
                .no-data {{
                    text-align: center;
                    color: #6c757d;
                    font-style: italic;
                    padding: 40px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 AI Trading Agent Report</h1>
                    <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p>Cycle Duration: {data.get('cycle_duration', 'N/A')} seconds</p>
                </div>

                <div class="section">
                    <h2>💰 Account Summary</h2>
                    <div class="metrics">
                        <div class="metric">
                            <span class="metric-value">${data.get('account', {}).get('cash', '0.00')}</span>
                            <span class="metric-label">Cash Balance</span>
                        </div>
                        <div class="metric">
                            <span class="metric-value">{len(data.get('positions', []))}</span>
                            <span class="metric-label">Positions</span>
                        </div>
                        <div class="metric">
                            <span class="metric-value">{data.get('total_trades', 0)}</span>
                            <span class="metric-label">Total Trades</span>
                        </div>
                        <div class="metric">
                            <span class="metric-value">{data.get('win_rate', '0.0')}%</span>
                            <span class="metric-label">Win Rate</span>
                        </div>
                    </div>
                </div>

                <div class="section">
                    <h2>📋 Pending Orders</h2>
                    {self._format_orders(data.get('orders', []))}
                </div>

                <div class="section">
                    <h2>📊 Trading Decisions</h2>
                    {self._format_decisions(data.get('decisions', {}))}
                </div>

                <div class="section">
                    <h2>⚡ Actions Taken</h2>
                    {self._format_actions(data.get('actions_taken', {}))}
                </div>

                <div class="section">
                    <h2>📰 Market Intelligence</h2>
                    {self._format_news_data(data.get('news_data', {}))}
                </div>

                <div class="section">
                    <h2>📈 Technical Analysis</h2>
                    {self._format_technical_data(data.get('technical_analysis', {}))}
                </div>

                <div class="section">
                    <h2>🎯 AI Reasoning</h2>
                    {self._format_ai_reasoning(data.get('ai_reasoning', {}))}
                </div>

                <div class="footer">
                    <p>🚀 Powered by AI Trading Agent | Real-time market analysis and automated execution</p>
                    <p>Generated by Composio AI Agent Framework</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _format_decisions(self, decisions):
        """Format trading decisions for email."""
        if not decisions:
            return "<p>No decisions made this cycle.</p>"

        html = ""
        for symbol, decision_data in decisions.items():
            decision = decision_data.get('decision', 'UNKNOWN')
            css_class = self._get_decision_class(decision)

            html += f"""
            <div class="{css_class}">
                <strong>{symbol}:</strong> {decision}
                {self._format_position_details(decision_data)}
            </div>
            """

        return html

    def _format_actions(self, actions_taken):
        """Format actions taken for email."""
        if not actions_taken:
            return "<p>No actions taken this cycle.</p>"

        html = ""
        for symbol, action in actions_taken.items():
            action_type = action.get('action', 'UNKNOWN')
            css_class = self._get_decision_class(action_type)

            html += f"""
            <div class="{css_class}">
                <strong>{symbol}:</strong> {action_type}
                {self._format_action_details(action)}
            </div>
            """

        return html

    def _format_news_data(self, news_data):
        """Format news and market intelligence."""
        if not news_data:
            return "<p>No recent news data available.</p>"

        html = "<ul>"
        for source, news in news_data.items():
            html += f"<li><strong>{source}:</strong> {news[:200]}...</li>"
        html += "</ul>"

        return html

    def _format_orders(self, orders):
        """Format pending orders for email."""
        if not orders:
            return "<p class='no-data'>No pending orders.</p>"

        html = """
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Order Type</th>
                    <th>Side</th>
                    <th>Quantity</th>
                    <th>Price</th>
                    <th>Status</th>
                    <th>Submitted</th>
                </tr>
            </thead>
            <tbody>
        """

        for order in orders:
            symbol = order.get('symbol', 'N/A')
            order_type = order.get('type', 'N/A')
            side = order.get('side', 'N/A')
            qty = order.get('qty', 'N/A')
            limit_price = order.get('limit_price', '')
            stop_price = order.get('stop_price', '')
            status = order.get('status', 'N/A')
            submitted_at = order.get('submitted_at', 'N/A')

            # Format price display
            price_display = ""
            if limit_price:
                price_display = f"Limit: ${float(limit_price):.2f}"
            elif stop_price:
                price_display = f"Stop: ${float(stop_price):.2f}"
            else:
                price_display = "Market"

            # Format submitted time
            if submitted_at and submitted_at != 'N/A':
                try:
                    submitted_dt = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                    submitted_display = submitted_dt.strftime('%m/%d %H:%M')
                except:
                    submitted_display = submitted_at[:16]  # Fallback
            else:
                submitted_display = 'N/A'

            html += f"""
                <tr>
                    <td><strong>{symbol}</strong></td>
                    <td>{order_type.title()}</td>
                    <td>{side.title()}</td>
                    <td>{qty}</td>
                    <td>{price_display}</td>
                    <td>{status.title()}</td>
                    <td>{submitted_display}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _format_technical_data(self, technical_data):
        """Format technical analysis data with explanations for beginners."""
        if not technical_data:
            return "<p>No technical analysis data available.</p>"

        html = ""
        for symbol, indicators in technical_data.items():
            html += f"<h3>{symbol} Technical Indicators:</h3><ul>"
            for indicator, value in indicators.items():
                explanation = self._explain_indicator(indicator, value)
                html += f"<li><strong>{indicator.upper()}:</strong> {value} - {explanation}</li>"
            html += "</ul>"

        return html

    def _explain_indicator(self, indicator, value):
        """Explain technical indicators in simple terms for beginners."""
        try:
            if indicator.lower() == 'rsi':
                rsi_val = float(value)
                if rsi_val < 30:
                    return "📉 RSI below 30 means the stock is OVERSOLD (might be a good time to BUY as it's cheap)"
                elif rsi_val > 70:
                    return "📈 RSI above 70 means the stock is OVERBOUGHT (might be a good time to SELL as it's expensive)"
                else:
                    return "🟡 RSI between 30-70 means the stock is fairly valued (normal trading range)"
            elif indicator.lower() == 'ema':
                return f"📊 Exponential Moving Average - shows the average price over time, smoothing out daily ups and downs"
            elif indicator.lower() == 'atr':
                atr_val = float(value)
                if atr_val < 0.5:
                    return "🟢 Low volatility - stock price doesn't move much (stable but slow)"
                elif atr_val < 2.0:
                    return "🟡 Medium volatility - normal price movement"
                else:
                    return "🔴 High volatility - stock price moves a lot (risky but potentially profitable)"
            elif indicator.lower() == 'volatility_score':
                vol_val = float(value)
                if vol_val < 2:
                    return "🟢 Low risk - price doesn't swing much"
                elif vol_val < 5:
                    return "🟡 Medium risk - normal price swings"
                else:
                    return "🔴 High risk - big price swings (be careful!)"
            elif indicator.lower() in ['c', 'close']:
                return f"💰 Current/Close Price - the last price the stock traded at (${value})"
            elif indicator.lower() in ['h', 'high']:
                return f"📈 Daily High - the highest price the stock reached today (${value})"
            elif indicator.lower() in ['l', 'low']:
                return f"📉 Daily Low - the lowest price the stock reached today (${value})"
            elif indicator.lower() in ['o', 'open']:
                return f"🚀 Opening Price - the price when trading started today (${value})"
            elif indicator.lower() in ['v', 'volume']:
                return f"📊 Trading Volume - how many shares were traded today ({value:,} shares)"
            elif indicator.lower() in ['vw', 'vwap']:
                return f"⚖️ VWAP - Volume Weighted Average Price - average price weighted by volume (${value})"
            elif indicator.lower() in ['n', 'count']:
                return f"🔢 Trade Count - number of individual trades today ({value})"
            else:
                return f"Technical indicator measuring {indicator}"
        except:
            return f"Technical indicator: {indicator}"

    def _format_news_data(self, news_data):
        """Format news and market intelligence data."""
        if not news_data:
            return "<p>No news data available.</p>"

        html = ""
        for symbol, news_items in news_data.items():
            if news_items and isinstance(news_items, list):
                html += f"<h3>📰 Latest News for {symbol}:</h3><ul>"
                for item in news_items[:5]:  # Show top 5 news items
                    title = item.get('title', 'No title')
                    summary = item.get('summary', 'No summary')
                    sentiment = item.get('sentiment', 'neutral')
                    sentiment_emoji = "🟢" if sentiment == "positive" else "🔴" if sentiment == "negative" else "🟡"

                    # Clean up the title and summary
                    title = title.replace('\\', '').strip()
                    summary = summary.replace('\\', '').strip()

                    # Show full summary if it's not too long, otherwise truncate nicely
                    if len(summary) > 200:
                        summary = summary[:200] + "..."
                    elif len(summary) < 50:
                        summary = summary  # Keep short summaries as-is

                    html += f"<li><strong>{sentiment_emoji} {title}</strong><br><small>{summary}</small></li>"
                html += "</ul>"
            else:
                html += f"<h3>📰 News for {symbol}:</h3><p>No recent news available</p>"

        return html

    def _format_ai_reasoning(self, ai_reasoning):
        """Format AI decision reasoning."""
        if not ai_reasoning:
            return "<p>No detailed AI reasoning available.</p>"

        html = ""
        for symbol, reasoning in ai_reasoning.items():
            html += f"<h3>{symbol}:</h3><p>{reasoning}</p>"

        return html

    def _get_decision_class(self, decision):
        """Get CSS class for decision type."""
        decision_lower = decision.lower()
        if 'buy' in decision_lower:
            return 'buy'
        elif 'sell' in decision_lower:
            return 'sell'
        elif 'hold' in decision_lower:
            return 'hold'
        else:
            return 'decision'

    def _format_position_details(self, decision_data):
        """Format position details for display."""
        position = decision_data.get('position', {})
        indicators = decision_data.get('indicators', {})

        details = []
        try:
            current_price = float(position.get('current_price', 0))
            details.append(f"Price: ${current_price:.2f}")
        except (ValueError, TypeError):
            details.append(f"Price: {position.get('current_price', 'N/A')}")
        
        try:
            qty = int(float(position.get('qty', 0)))
            details.append(f"Qty: {qty}")
        except (ValueError, TypeError):
            details.append(f"Qty: {position.get('qty', 'N/A')}")
        
        try:
            unrealized_plpc = float(position.get('unrealized_plpc', 0))
            details.append(f"P&L: {unrealized_plpc:.2f}%")
        except (ValueError, TypeError):
            details.append(f"P&L: {position.get('unrealized_plpc', 'N/A')}%")

        if indicators:
            key_indicators = []
            for indicator, value in indicators.items():
                try:
                    if isinstance(value, (int, float)):
                        key_indicators.append(f"{indicator}: {value:.2f}")
                    else:
                        key_indicators.append(f"{indicator}: {value}")
                except:
                    key_indicators.append(f"{indicator}: {value}")
            if key_indicators:
                details.append(f"Indicators: {', '.join(key_indicators)}")

        return f"<br><small>{' | '.join(details)}</small>" if details else ""

    def _format_action_details(self, action):
        """Format action details for display."""
        details = []
        if action.get('shares'):
            details.append(f"Shares: {action['shares']}")
        if action.get('limit_price'):
            details.append(f"Limit: ${action['limit_price']:.2f}")
        if action.get('take_profit'):
            details.append(f"Take Profit: ${action['take_profit']:.2f}")
        if action.get('stop_loss'):
            details.append(f"Stop Loss: ${action['stop_loss']:.2f}")

        return f"<br><small>{' | '.join(details)}</small>" if details else ""

# Global email agent instance
email_agent = EmailAgent()