# telegram_sync.py

import requests
import os
import re

# Load config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7856499764:AAHEDWJaz1KukBn-2gjVx5ea0LHfZPZpFoI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7930119115")


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2"""
    # List of characters to escape
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


def send_sync(message: str):
    """Send a message to Telegram using MarkdownV2 with proper escaping"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram: Missing BOT_TOKEN or CHAT_ID")
        return

    # Escape message for MarkdownV2
    escaped_message = escape_markdown_v2(message)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": escaped_message,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram alert sent")
        else:
            print(f"❌ Telegram API error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")
