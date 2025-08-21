# main.py

"""
AI Trader Web Server
- Embedded send_sync to avoid import issues
- Full buy/sell cycle with dynamic watchlist
"""

import os
import logging
from flask import Flask, jsonify
from datetime import datetime
import requests

# === CONFIGURE LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
app = Flask(__name__)

# === EMBEDDED TELEGRAM SEND FUNCTION ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7856499764:AAHEDWJaz1KukBn-2gjVx5ea0LHfZPZpFoI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7930119115")


def send_sync(message: str):
    """Send message to Telegram with MarkdownV2 escaping"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("❌ Telegram: Missing BOT_TOKEN or CHAT_ID")
        return

    # Escape MarkdownV2 special characters
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
            logging.info("✅ Telegram alert sent")
        else:
            logging.error(f"❌ Telegram API error: {response.status_code}, {response.text}")
    except Exception as e:
        logging.error(f"❌ Failed to send Telegram: {e}")


# === DYNAMIC WATCHLIST ===
def get_watchlist():
    """Return a fallback watchlist"""
    return ["RARE", "NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "META", "AMD"]


# === POLITICAL BUY CHECK ===
def is_political_buy(symbol: str) -> bool:
    return symbol == "RARE"  # Simulated


# === MODULE LOADER ===
def get_modules():
    """Import fusion engine"""
    global generate_fused_signal, execute_paper_trade, generate_exit_signal
    try:
        from app.signals.fusion import generate_fused_signal, execute_paper_trade, generate_exit_signal
        logging.info("✅ Fusion engine loaded")
    except Exception as e:
        logging.critical(f"💥 Failed to load fusion engine: {e}")
        raise


# === ROUTES ===
@app.route("/run-daily")
def run_daily():
    try:
        logging.info("🔁 /run-daily triggered")
        send_sync("🔁 Daily cycle started")

        get_modules()

        # 1. Check for exits
        from app.signals.fusion import load_open_positions, save_open_positions
        positions = load_open_positions()
        remaining_positions = []

        for pos in positions:
            symbol = pos["symbol"]
            exit_signal = generate_exit_signal(
                symbol=symbol,
                entry_price=pos["entry_price"],
                stop_loss=pos["stop_loss"],
                qty=pos["qty"]
            )
            if exit_signal:
                exit_signal["symbol"] = symbol
                execute_paper_sell(exit_signal)
            else:
                remaining_positions.append(pos)
        save_open_positions(remaining_positions)

        # 2. Check for new buys
        watchlist = get_watchlist()
        for symbol in watchlist:
            political = is_political_buy(symbol)
            signal = generate_fused_signal(symbol, political_buy=political)
            if signal:
                execute_paper_trade(signal)

        # 3. Self-learning
        try:
            from app.learning.self_learning import update_signal_weights
            update_signal_weights()
        except Exception as e:
            logging.error(f"❌ Self-learning failed: {e}")

        send_sync("✅ Daily cycle complete")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        logging.error(f"💥 Error: {e}", exc_info=True)
        try:
            send_sync(f"❌ Run failed: {type(e).__name__}")
        except:
            pass
        return jsonify({"status": "error"}), 500


@app.route("/")
def home():
    return jsonify({"status": "online"})


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


# === START SERVER ===
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
