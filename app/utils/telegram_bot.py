# app/utils/telegram_bot.py

"""
Telegram Bot for Kill Switch
Listens for /pause, /resume, /status
Exports start_bot() for use in main.py
"""

import logging
from flask import Flask, request
import json
from threading import Thread

# Paths
STATE_FILE = "trading_logs/trading_state.json"

# Your Telegram bot token and allowed chat ID
BOT_TOKEN = "7856499764:AAHEDWJaz1KukBn-2gjVx5ea0LHfZPZpFoI"
ALLOWED_CHAT_ID = "7856499764"  # Replace with your actual Telegram user/chat ID

app = Flask(__name__)


def load_state():
    """Load current trading state. Default: enabled."""
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("enabled", True)
    except Exception:
        return True  # Default: trading enabled


def save_state(enabled: bool):
    """Save trading state to disk."""
    import os
    os.makedirs("trading_logs", exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"enabled": enabled}, f, indent=2)


@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram messages."""
    try:
        data = request.get_json()
        if not data:  # ✅ Fixed: was incomplete
            return {"status": "no data"}, 200

        message = data.get("message", {})
        chat_id = str(message.get("chat", {}).get("id"))
        text = message.get("text", "").strip()

        # Security: Only respond to your chat
        if chat_id != ALLOWED_CHAT_ID:
            logging.warning(f"⚠️ Unauthorized access attempt from chat_id: {chat_id}")
            return {"status": "unauthorized"}, 200

        current_state = load_state()

        if text == "/pause":
            if not current_state:
                send_message(chat_id, "🛑 Trading is already paused.")
            else:
                save_state(False)
                send_message(chat_id, "🛑 Trading paused. No new trades will be executed.")
            return {"status": "paused"}, 200

        elif text == "/resume":
            if current_state:
                send_message(chat_id, "✅ Trading is already running.")
            else:
                save_state(True)
                send_message(chat_id, "✅ Trading resumed. New trades are allowed.")
            return {"status": "resumed"}, 200

        elif text == "/status":
            status = "✅ Trading: ENABLED" if current_state else "🛑 Trading: PAUSED"
            send_message(chat_id, f"📊 Status: {status}")
            return {"status": "status_sent"}, 200

        else:
            return {"status": "ignored"}, 200

    except Exception as e:
        logging.error(f"❌ Error in Telegram bot: {e}")
        return {"status": "error"}, 500


def send_message(chat_id: str, text: str):
    """Send a message via Telegram bot."""
    import requests
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        logging.error(f"❌ Failed to send Telegram message: {e}")


def start_bot():
    """
    Start the Telegram bot in a background thread.
    Called from main.py.
    """
    def run():
        app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

    thread = Thread(target=run, daemon=True)
    thread.start()
    logging.info("🤖 Telegram bot started in background")
