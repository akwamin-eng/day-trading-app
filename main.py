# main.py

"""
Elite AI Trader
Phase 5: Signal Fusion & Paper Trading
✅ Runs on Cloud Run
✅ Listens on PORT
✅ Serves /health and /run-daily
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

# Import modules (delayed to avoid startup delay)
def get_modules():
    global send_sync, load_state, generate_fused_signal, execute_paper_trade
    from app.utils.telegram_alerts import send_sync
    from app.utils.trading_state import load_state
    from app.signals.fusion import generate_fused_signal, execute_paper_trade

# Paths
LOGS_DIR = "trading_logs"

# Create Flask app
app = Flask(__name__)

# Start Telegram alerts (no bot, just send_sync)
try:
    from app.utils.telegram_alerts import send_sync
    send_sync("🔄 AI Trader service started (waiting for /run-daily)")
except Exception as e:
    logging.error(f"❌ Failed to initialize Telegram: {e}")


def log_trade(symbol: str, signals: dict, confidence: float, action: str = "buy"):
    """Log a trade decision."""
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
    try:
        get_modules()
        logging.info("🔁 /run-daily triggered")
        send_sync("🔄 AI Trader: Daily cycle started")

        # Check if trading is paused
        current_trading_enabled = load_state()
        if not current_trading_enabled:
            msg = "🛑 Trading is paused. No trades will be executed."
            logging.warning(msg)
            send_sync(msg)
            return {"status": "paused"}, 200

        # List of stocks to monitor
        watchlist = ["RARE", "NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "META", "AMD"]
        political_buys = ["RARE"]  # Simulated

        executed_trades = 0

        for symbol in watchlist:
            try:
                political_buy = symbol in political_buys
                signal = generate_fused_signal(symbol, political_buy=political_buy)

                if signal:
                    execute_paper_trade(signal)
                    log_trade(
                        symbol=symbol,
                        confidence=signal["confidence"],
                        signals={
                            "political": political_buy,
                            "sentiment": True,
                            "fundamentals": True,
                            "technical": True
                        }
                    )
                    executed_trades += 1
                else:
                    logging.info(f"❌ No signal for {symbol}")

            except Exception as e:
                logging.error(f"❌ Error processing {symbol}: {e}")

        logging.info(f"✅ Daily cycle complete. {executed_trades} trades executed.")
        send_sync(f"📊 Daily Summary: {executed_trades} trades executed.")
        return {"status": "success", "trades": executed_trades}, 200

    except Exception as e:
        logging.critical(f"💥 Critical error in /run-daily: {e}", exc_info=True)
        send_sync(f"🛑 AI Trader crashed: {type(e).__name__}: {e}")
        return {"status": "error", "error": str(e)}, 500


# Run the web server (required for Cloud Run)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
