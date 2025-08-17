# app/utils/telegram_alerts.py

import requests
import os
import logging

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7856499764:AAHEDWJaz1KukBn-2gjVx5ea0LHfZPZpFoI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7930119115")
SEND_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def send_sync(message: str):
    """Send a message via Telegram using direct HTTP."""
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(SEND_URL, data=payload, timeout=10)
        if resp.status_code == 200:
            logging.info("✅ Telegram alert sent")
        else:
            logging.error(f"❌ Telegram API error: {resp.status_code} - {resp.text}")
    except Exception as e:
        logging.error(f"❌ Failed to send Telegram message: {e}")
