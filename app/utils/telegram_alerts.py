# app/utils/telegram_alerts.py

"""
Telegram Alert System (Fixed for v21.7)
- No use of removed methods like is_initialized
- Clean event loop per call
- Proper shutdown
"""

import asyncio
import logging
from telegram import Bot

# Set up logging
logging.basicConfig(level=logging.INFO)

# --- Configuration ---
TELEGRAM_TOKEN = "7856499764:AAHEDWJaz1KukBn-2gjVx5ea0LHfZPZpFoI"
CHAT_ID = "7930119115"


async def _send_message_once(message: str):
    """Send a message with a fresh Bot and session."""
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        await bot.initialize()  # Start session
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )
        logging.info("✅ Telegram alert sent")
    except Exception as e:
        logging.error(f"❌ Failed to send Telegram message: {e}")
    finally:
        await bot.shutdown()  # Always clean up


def send_sync(message: str):
    """Synchronous wrapper with clean event loop."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_send_message_once(message))
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
    except Exception as e:
        logging.error(f"❌ Sync wrapper failed: {e}")
