# telegram_sync.py
import requests
import os
import re
import logging  # ✅ This was missing!

# Setup logging if not already configured
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def escape_md(text: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+-=|{}.!])', r'\\\1', text)

def send_sync(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("❌ Telegram: Missing BOT_TOKEN or CHAT_ID")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": escape_md(message),
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            logging.info("✅ Telegram alert sent")
        else:
            logging.error(f"❌ Telegram API error: {resp.status_code}, {resp.text}")
    except Exception as e:
        logging.error(f"❌ Failed to send Telegram: {e}")
