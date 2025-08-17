# app/utils/telegram_bot.py

"""
Telegram Bot for Kill Switch
Listens for /pause, /resume, /status
"""

import logging
from flask import Flask, request
import json
from app.utils.trading_state import save_state, load_state
from app.utils.telegram_alerts import send_sync

app = Flask(__name__)

# Store your allowed chat ID (for security)
ALLOWED_CHAT_ID = "7856499764"  # Replace with your actual Telegram chat/user ID

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        if not data:
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
                send_sync("🛑 Trading is already paused.")
            else:
                save_state(False)
                send_sync("🛑 Trading paused. No new trades will be executed.")
            return {"status": "paused"}, 200

        elif text == "/resume":
            if current_state:
                send_sync("✅ Trading is already running.")
            else:
                save_state(True)
                send_sync("✅ Trading resumed. New trades are allowed.")
            return {"status": "resumed"}, 200

        elif text == "/status":
            status = "✅ Trading: ENABLED" if current_state else "🛑 Trading: PAUSED"
            send_sync(f"📊 Status: {status}")
            return {"status": "status_sent"}, 200

        else:
            # Ignore other messages
            return {"status": "ignored"}, 200

    except Exception as e:
        logging.error(f"❌ Error in Telegram bot: {e}")
        return {"status": "error"}, 500

# For testing
if __name__ == "__main__":
    app.run(port=8080)
