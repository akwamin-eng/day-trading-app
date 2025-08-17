# main.py

"""
Elite AI Trader
Phase 5: Signal Fusion & Paper Trading
Runs daily, executes high-conviction paper trades.
"""

import logging
import sys
from datetime import datetime
from typing import List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Import modules
from app.signals.fusion import generate_fused_signal, execute_paper_trade
from app.utils.telegram_alerts import send_sync
from app.learning.self_learning import update_strategy_weights


def log_startup():
    """Log system startup."""
    logging.info("🚀 Elite AI Trader: Phase 5 - Signal Fusion & Paper Trading")
    logging.info(f"📅 Run started at {datetime.utcnow().isoformat()}")
    send_sync(f"🔄 AI Trader: Daily cycle started at {datetime.now().strftime('%H:%M')}")


def run_daily_trading_cycle():
    """Main trading loop: generate signals and execute paper trades."""
    log_startup()

    # List of stocks to monitor
    watchlist = ["RARE", "NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "META", "AMD"]

    # Simulate political buys from FMP (replace with real data later)
    political_buys = ["RARE", "NVDA"]  # Example: Rep bought RARE

    executed_trades = 0

    for symbol in watchlist:
        try:
            # Generate fused signal
            political_buy = symbol in political_buys
            signal = generate_fused_signal(symbol, political_buy=political_buy)

            if signal:
                execute_paper_trade(signal)
                executed_trades += 1
            else:
                logging.info(f"❌ No signal for {symbol}")

        except Exception as e:
            logging.error(f"❌ Error processing {symbol}: {e}")
            send_sync(f"🚨 Error processing {symbol}: {e}")

    logging.info(f"✅ Daily cycle complete. {executed_trades} trades executed.")
    send_sync(f"📊 Daily Summary: {executed_trades} trades executed.")


def run_weekly_review():
    """
    Weekly AI review: analyze performance and update strategy.
    Runs every Sunday at 9 PM.
    """
    today = datetime.now().weekday()  # 0 = Monday, 6 = Sunday
    hour = datetime.now().hour

    if today == 6 and 20 <= hour < 22:  # Sunday, 8–10 PM
        logging.info("📅 Running weekly AI review and self-learning update...")
        send_sync("📅 Starting weekly AI review...")

        try:
            update_strategy_weights()
            send_sync("✅ Weekly AI review complete. Strategy updated.")
        except Exception as e:
            logging.error(f"❌ Weekly review failed: {e}")
            send_sync(f"🚨 Weekly review failed: {e}")


if __name__ == "__main__":
    try:
        # Run daily trading cycle
        run_daily_trading_cycle()

        # Optional: Run weekly review
        run_weekly_review()

    except Exception as e:
        logging.critical(f"💥 Critical error in main loop: {e}")
        send_sync(f"🛑 AI Trader crashed: {e}")
        sys.exit(1)
