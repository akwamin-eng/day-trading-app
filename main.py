# main.py
"""
Production entry point for AI trading system.
Starts all services + health server + Telegram alerts.
"""

import os
import subprocess
import time
import signal
import sys
import threading
from datetime import datetime
from app.utils.telegram_alerts import send_sync

# Local modules
from app.utils.config import get_config
from app.utils.telegram import (
    market_closed_alert,
    market_open_alert,
    market_close_summary
)
from app.utils.market_hours import is_market_open, wait_until_market_open, wait_until_market_close

# Flask for health checks (required by Cloud Run)
from flask import Flask
app = Flask(__name__)

@app.route("/")
@app.route("/health")
def health():
    return {"status": "healthy", "service": "ai-trader", "timestamp": datetime.now().isoformat()}, 200

def start_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Global state
in_trading_session = False
daily_trades = 0
starting_balance = 100000.0  # Will be updated from Alpaca on market open

# Get account value from Alpaca (simplified)
def get_account_value():
    """
    Placeholder: Replace with real Alpaca API call.
    """
    try:
        # Example: from alpaca.trading.client import TradingClient
        # client = TradingClient(api_key, secret_key, paper=True)
        # account = client.get_account()
        # return float(account.equity)
        return 100000.0  # Mock value
    except Exception as e:
        print(f"❌ Failed to fetch account value: {e}")
        return starting_balance

# Background task: Send hourly health check when market is closed
def telegram_health_loop():
    while True:
        if not is_market_open():
            market_closed_alert()
            time.sleep(3600)  # Wait 1 hour
        else:
            time.sleep(60)  # Check every minute when open

# Background task: Monitor market open/close for alerts
def trading_session_monitor():
    global in_trading_session, starting_balance, daily_trades

    while True:
        if is_market_open():
            if not in_trading_session:
                # Market just opened
                starting_balance = get_account_value()
                market_open_alert(starting_balance)
                in_trading_session = True
                daily_trades = 0
                print("✅ Trading session started.")
        else:
            if in_trading_session:
                # Market just closed
                ending_balance = get_account_value()
                daily_pnl = ending_balance - starting_balance
                market_close_summary(ending_balance, daily_pnl, daily_trades)
                in_trading_session = False
                print("📌 Daily summary sent. Waiting for next market open.")
        time.sleep(60)

# List of services to run
SERVICES = [
    "python -c 'from app.data.ingest import start_ingest; start_ingest()'",
    "python -c 'from app.features.subscriber import start_feature_subscriber; start_feature_subscriber()'",
    "python -c 'from app.sentiment.fetcher import start_news_sentiment_pipeline; start_news_sentiment_pipeline()'",
    "python -c 'from app.ml.subscriber import start_ml_merger; start_ml_merger()'",
    "python -c 'from app.execution.executor import start_executor; start_executor()'"
]

processes = []

def signal_handler(signum, frame):
    print("\n🛑 Shutting down all services...")
    for p in processes:
        p.terminate()
    for p in processes:
        p.wait()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    print("🚀 Starting AI Trading System...")

    # Start Flask health server
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    print("✅ Health check server started on /health")

    # Start Telegram alert loops
    health_alert_thread = threading.Thread(target=telegram_health_loop, daemon=True)
    health_alert_thread.start()
    print("✅ Hourly Telegram health alerts enabled")

    monitor_thread = threading.Thread(target=trading_session_monitor, daemon=True)
    monitor_thread.start()
    print("✅ Trading session monitor started")

    # Stagger startup of services
    for cmd in SERVICES:
        print(f"✅ Starting: {cmd}")
        p = subprocess.Popen(cmd, shell=True)
        processes.append(p)
        time.sleep(2)

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
