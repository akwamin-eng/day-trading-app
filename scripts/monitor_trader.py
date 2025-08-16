#!/usr/bin/env python3
"""
AI Trader Monitor Script
Runs the trading system locally with full visibility into:
- Sentiment analysis
- Position sizing
- Trade execution
- Telegram alerts
- Alpaca account status
"""

import time
import logging
import os
import sys
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)

# Suppress verbose logs from libraries
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("google.auth").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def print_header(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f" {title.upper()}")
    print("=" * 60)


def test_sentiment():
    """Test FinBERT sentiment analysis with sample news."""
    print_header("FinBERT Sentiment Test")
    try:
        from app.sentiment.finbert import analyze_sentiment
        test_cases = [
            "Apple reports record earnings and raises guidance.",
            "Company files for bankruptcy after massive losses.",
            "Stock prices moved slightly today with no major news."
        ]
        for text in test_cases:
            result = analyze_sentiment(text)
            print(f"📝 {text}")
            print(f"📊 Sentiment: {result['label']} (Score: {result['score']:.3f})\n")
    except Exception as e:
        logging.error(f"❌ Sentiment test failed: {e}")


def test_position_size():
    """Test dynamic position sizing for key symbols."""
    print_header("Position Sizing Test")
    try:
        from app.risk.position import get_position_size
        symbols = ["AAPL", "TSLA", "MSFT", "GOOGL"]
        for symbol in symbols:
            size = get_position_size(symbol)
            print(f"📈 {symbol}: {size} shares")
    except Exception as e:
        logging.error(f"❌ Position sizing test failed: {e}")


def test_alpaca_connection():
    """Test connection to Alpaca paper trading API."""
    print_header("Alpaca Paper Account Status")
    try:
        from alpaca.trading.client import TradingClient
        from app.utils.secrets import get_paper_api_key, get_paper_secret_key
        client = TradingClient(get_paper_api_key(), get_paper_secret_key(), paper=True)
        account = client.get_account()
        print(f"🏦 Status: {account.status}")
        print(f"💵 Equity: ${float(account.equity):,.2f}")
        print(f"📊 Buying Power: ${float(account.buying_power):,.2f}")
        print(f"📊 Portfolio Value: ${float(account.portfolio_value):,.2f}")
    except Exception as e:
        logging.error(f"❌ Alpaca connection failed: {e}")


def test_telegram_alert():
    """Send a test alert to Telegram."""
    print_header("Telegram Alert Test")
    try:
        from app.utils.telegram_alerts import send_sync
        message = f"""
🧪 **Local Trader Monitor Running**
📅 {datetime.now().strftime('%Y-%m-%d')}
🕒 {datetime.now().strftime('%H:%M:%S')}
✅ All systems connected
📊 Ready for signals
🔁 Refreshing every 60 seconds
        """.strip()
        send_sync(message)
        logging.info("✅ Telegram test alert sent!")
    except Exception as e:
        logging.error(f"❌ Telegram test failed: {e}")


def run_diagnostics():
    """Run all diagnostic tests."""
    test_sentiment()
    test_position_size()
    test_alpaca_connection()
    test_telegram_alert()


def run_monitor():
    """Run the monitor loop with auto-refresh."""
    print_header("AI TRADING SYSTEM MONITOR")
    print(f"📍 Current Directory: {os.getcwd()}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
    print(f"🔄 Running diagnostics...")

    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')  # Clear screen
            run_diagnostics()
            print(f"\n🔁 Refreshing in 60 seconds... Press Ctrl+C to exit.")
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n👋 AI Trader Monitor stopped. Have a great day!")


if __name__ == "__main__":
    run_monitor()
