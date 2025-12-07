# AI Trading Bot Deployment Guide

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file with your API keys:
```
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key
COMPOSIO_API_KEY=your_composio_api_key
AUTO_START_TRADING=false  # Set to 'true' for auto-start
```

### 3. Run the Application
```bash
python app.py
```

## Current Behavior
By default, the trading bot **does NOT start automatically** when deployed. It requires manual activation through the dashboard.

## Auto-Start Options

### Option 1: Manual Control (Current Default)
- Trading only starts when you click "Start Trading" in the dashboard
- Gives you full control over when trading begins
- Safer for testing and development

### Option 2: Auto-Start on Deployment
To enable automatic trading startup, set the environment variable:

```bash
# Linux/Mac
export AUTO_START_TRADING=true
python app.py

# Windows PowerShell
$env:AUTO_START_TRADING="true"
python app.py

# Windows CMD
set AUTO_START_TRADING=true
python app.py
```

### Option 3: Production Deployment
For production deployment with auto-start:

```bash
# Using systemd (Linux)
sudo nano /etc/systemd/system/ai-trading.service

[Unit]
Description=AI Trading Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/ai-trading-bot
Environment=AUTO_START_TRADING=true
ExecStart=/path/to/python app.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable ai-trading
sudo systemctl start ai-trading
```

## Safety Recommendations

1. **Test First**: Always test in manual mode before enabling auto-start
2. **Monitor Logs**: Check application logs regularly when auto-start is enabled
3. **Risk Management**: Ensure your risk settings are appropriate for automated trading
4. **Backup**: Have manual override capability

## Current Status
- ✅ Dashboard loads and displays data
- ✅ Manual trading controls work
- ✅ Auto-start capability added (disabled by default)
- ✅ All JavaScript errors fixed