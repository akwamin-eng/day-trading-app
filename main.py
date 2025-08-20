# main.py

"""
AI Trader Web Server
✅ Self-contained: No broken imports
✅ Works: Sends Telegram alerts
✅ Ready: For dynamic watchlist and fusion
"""

import os
import logging
from flask import Flask, jsonify
from datetime import datetime
from app.learning.self_learning import update_signal_weights
import requests

# === CONFIGURE LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === GLOBAL VARS ===
app = Flask(__name__)

# --- 🔥 EMBEDDED TELEGRAM SEND FUNCTION ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7856499764:AAHEDWJaz1KukBn-2gjVx5ea0LHfZPZpFoI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7930119115")

def send_sync(message: str):
    """Send a message to Telegram — embedded to avoid import issues"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("❌ Telegram: Missing BOT_TOKEN or CHAT_ID")
        return

    # Escape for MarkdownV2
    escaped = message.replace('-', '\\-').replace('.', '\\.').replace('!', '\\!').replace('(', '\\(').replace(')', '\\)')
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": escaped,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Telegram alert sent")
        else:
            logger.error(f"❌ Telegram API error: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"❌ Failed to send Telegram: {e}")

# Delayed imports (set after modules load)
generate_fused_signal = None
execute_paper_trade = None


# === DYNAMIC WATCHLIST ===
def get_watchlist():
    """Get today's dynamic watchlist from FMP screener"""
    try:
        from app.data.pipelines.dynamic_watchlist import build_dynamic_watchlist
        return build_dynamic_watchlist()
    except Exception as e:
        logger.warning(f"⚠️ Dynamic watchlist failed: {e}. Using fallback.")
        return ["RARE", "NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "META", "AMD"]


# === POLITICAL BUY CHECK ===
def is_political_buy(symbol: str) -> bool:
    """Check if a political buy occurred"""
    # Simulated — replace with real data later
    return symbol == "RARE"


# === MODULE LOADER ===
def get_modules():
    """Import fusion engine only"""
    global generate_fused_signal, execute_paper_trade

    try:
        from app.signals.fusion import generate_fused_signal, execute_paper_trade
        logger.info("✅ Signal fusion engine loaded")
    except Exception as e:
        logger.critical(f"💥 Failed to load fusion engine: {e}")
        raise


# === ROUTES ===
@app.route("/")
def home():
    return jsonify({"status": "online", "service": "AI Trader"})

@app.route("/run-daily")
def run_daily():
    try:
        logger.info("🔁 /run-daily triggered")
        send_sync("🔁 Daily cycle started")

        get_modules()
        watchlist = get_watchlist()
        trade_count = 0

        for symbol in watchlist:
            try:
                political = is_political_buy(symbol)
                logger.info(f"🔍 Evaluating {symbol} | Political Buy: {political}")
                signal = generate_fused_signal(symbol, political_buy=political)
                if signal:
                    execute_paper_trade(signal)
                    trade_count += 1
                else:
                    logger.info(f"❌ No signal for {symbol}")
            except Exception as e:
                logger.error(f"❌ Failed to evaluate {symbol}: {e}")
                continue

        # Final summary
        status = f"✅ Daily cycle complete. {trade_count} trades executed."
        logger.info(status)
        send_sync(status)

        # 🔁 Self-Learning: Update weights based on today's trades
        try:
            update_signal_weights()
            send_sync("🧠 Self-learning complete. Weights updated.")
        except Exception as e:
            logger.error(f"❌ Self-learning failed: {e}")
            send_sync("⚠️ Self-learning failed")

        return jsonify({"status": "success", "trades_executed": trade_count}), 200

    except Exception as e:
        logger.error(f"💥 Critical error in /run-daily: {e}", exc_info=True)
        send_sync(f"❌ Run failed: {type(e).__name__}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


# === START SERVER ===
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"✅ Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
