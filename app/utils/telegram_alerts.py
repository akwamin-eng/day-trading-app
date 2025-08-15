# app/utils/telegram.py

"""
Telegram Alert System
Sends secure alerts to Telegram using python-telegram-bot v21.7 (async).
Includes sync wrapper for use in non-async code.
"""

import asyncio
import logging
from telegram import Bot

# Set up logging
logging.basicConfig(level=logging.INFO)

# --- Configuration ---
# Option 1: Hardcoded (for quick setup)
TELEGRAM_TOKEN = "7856499764:AAHEDWJaz1KukBn-2gjVx5ea0LHfZPZpFoI"
CHAT_ID = "7930119115"

# Option 2: Use environment variables (recommended for production)
# import os
# TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "your-default-token")
# CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "your-default-chat-id")

# Initialize the bot
bot = Bot(token=TELEGRAM_TOKEN)


async def send_telegram_message(message: str):
    """
    Send a message to Telegram (async).
    """
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="Markdown"  # Optional: use Markdown for formatting
        )
        logging.info("✅ Telegram alert sent")
    except Exception as e:
        logging.error(f"❌ Failed to send Telegram message: {e}")


def send_sync(message: str):
    """
    Synchronous wrapper for sending Telegram messages.
    Use this in non-async functions (e.g., trade execution, risk management).
    """
    try:
        asyncio.run(send_telegram_message(message))
    except Exception as e:
        logging.error(f"❌ Failed to send Telegram message (sync wrapper): {e}")


# === Alert Functions ===

def market_open_alert(starting_balance: float):
    """
    Send alert when trading session starts.
    """
    message = f"""
🚀 **Market Open**  
✅ Trading has started  
💼 Starting Balance: ${starting_balance:,.2f}  
🧠 AI Trader is active  
🕒 {get_timestamp()}
    """.strip()
    send_sync(message)


def market_close_summary(ending_balance: float, daily_pnl: float, total_trades: int):
    """
    Send daily summary when market closes.
    """
    message = f"""
📌 **Market Closed - Daily Summary**  
📅 {get_date()}  
💼 Ending Balance: ${ending_balance:,.2f}  
📈 Daily PnL: ${daily_pnl:,.2f}  
📊 Total Trades: {total_trades}  
✅ AI Trader shutting down for the day  
🕒 {get_timestamp()}
    """.strip()
    send_sync(message)


def trade_executed(symbol: str, action: str, qty: int, price: float, confidence: float = 1.0):
    """
    Send alert when a trade is executed.
    """
    message = f"""
🎯 **Trade Executed**  
{action} {qty} shares of {symbol}  
💰 Price: ${price:.2f}  
📊 Confidence: {confidence:.2f}  
🕒 {get_timestamp()}
    """.strip()
    send_sync(message)


def trade_failed(symbol: str, signal: str, error: str):
    """
    Send alert when a trade fails.
    """
    message = f"""
🚨 **Trade Failed**  
{signal} {symbol}  
❌ Error: {error}  
🕒 {get_timestamp()}
    """.strip()
    send_sync(message)


def system_error(error: str):
    """
    Send alert on system error.
    """
    message = f"""
🛑 **System Error**  
{error}  
🕒 {get_timestamp()}
    """.strip()
    send_sync(message)


# === Helper Functions ===

def get_timestamp() -> str:
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_date() -> str:
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d')


# === Test Function (Optional) ===
if __name__ == "__main__":
    print("🧪 Testing Telegram alerts...")
    send_sync("🤖 Test: AI Trader is online and ready.")
    print("✅ Test message sent.")
