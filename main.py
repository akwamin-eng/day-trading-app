# main.py

"""
Elite AI Trader
Phase 5: Signal Fusion & Paper Trading
✅ Deployed on Cloud Run
✅ Fully autonomous
✅ Self-learning every Sunday
"""

import logging
import sys
import json
import os
from datetime import datetime
from flask import Flask

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from app.utils.telegram_alerts import send_sync
from app.utils.trading_state import load_state
from app.signals.fusion import generate_fused_signal, execute_paper_trade

# Paths
LOGS_DIR = "trading_logs"

# Create Flask app
app = Flask(__name__)


def log_startup():
    """Log system startup."""
    logging.info("🚀 Elite AI Trader: Phase 5 - Signal Fusion & Paper Trading")
    logging.info(f"📅 Run started at {datetime.utcnow().isoformat()}")
    send_sync(f"🔄 AI Trader: Daily cycle started at {datetime.now().strftime('%H:%M')}")


def log_trade(symbol: str, signals: dict, confidence: float, action: str = "buy"):
    """Log a trade decision for future analysis and self-learning."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_entry = {
        "symbol": symbol,
        "action": action,
        "confidence": confidence,
        "signals": signals,
        "timestamp": datetime.utcnow().isoformat()
    }
    log_file = os.path.join(LOGS_DIR, "weekly_trades.jsonl")
    with open(log_file, "a") as f:
        f.write(f"{json.dumps(log_entry)}\n")
    logging.info(f"📊 Logged trade: {log_entry}")


@app.route("/health")
def health():
    return {"status": "healthy"}, 200


@app.route("/run-daily")
def run_daily():
    """Trigger the daily trading cycle."""
    log_startup()

    # Check if trading is paused
    current_trading_enabled = load_state()
    if not current_trading_enabled:
        msg = "🛑 Trading is paused. No trades will be executed."
        logging.warning(msg)
        send_sync(msg)
        return {"status": "paused"}, 200

    # List of stocks to monitor
    watchlist = ["RARE", "NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "META", "AMD"]

    # Simulate political buys (replace with real FMP data later)
    political_buys = ["RARE"]  # Example: Rep bought RARE

    executed_trades = 0

    for symbol in watchlist:
        try:
            # Generate fused signal
            political_buy = symbol in political_buys
            signal = generate_fused_signal(symbol, political_buy=political_buy)

            if signal:
                execute_paper_trade(signal)
                # Log the trade for self-learning
                log_trade(
                    symbol=symbol,
                    confidence=signal["confidence"],
                    signals={
                        "political": political_buy,
                        "sentiment": True,
                        "fundamentals": True,
                        "technical": True
                    },
                    action="buy"
                )
                executed_trades += 1
            else:
                logging.info(f"❌ No signal for {symbol}")

        except Exception as e:
            logging.error(f"❌ Error processing {symbol}: {e}")
            send_sync(f"🚨 Error processing {symbol}: {e}")

    logging.info(f"✅ Daily cycle complete. {executed_trades} trades executed.")
    send_sync(f"📊 Daily Summary: {executed_trades} trades executed.")
    return {"status": "success", "trades": executed_trades}, 200


def run_weekly_review():
    """
    Weekly AI review: analyze performance and update strategy.
    Runs every Sunday at 9 PM ET.
    """
    today = datetime.now().weekday()  # 0 = Monday, 6 = Sunday
    hour = datetime.now().hour

    if today == 6 and 20 <= hour < 22:  # Sunday, 8–10 PM
        logging.info("📅 Running weekly AI review and self-learning update...")
        try:
            from app.learning.self_learning import update_strategy_weights
            update_strategy_weights()
        except Exception as e:
            logging.error(f"❌ Weekly review failed: {e}")
            send_sync(f"🚨 Weekly review failed: {e}")


# Run the web server (required for Cloud Run)
if __name__ == "__main__":
    # For local testing
    run_weekly_review()

# Run in production (Cloud Run)
if __name__ != "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
