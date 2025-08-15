# app/utils/telegram.py

"""
Send alerts to Telegram.
"""

import os
import time
import logging
from datetime import datetime
from telegram import Bot
from app.utils.config import get_config

# Load config
config = get_config()
TELEGRAM_TOKEN = config['telegram']['token']
CHAT_ID = config['telegram']['chat_id']

# Initialize bot
bot = Bot(token=TELEGRAM_TOKEN)

def send_telegram_message(message: str):
    """Send a message to Telegram."""
    try:
        bot.send_message(chat_id=CHAT_ID, text=message)
        logging.info("✅ Telegram alert sent")
    except Exception as e:
        logging.error(f"❌ Failed to send Telegram message: {e}")

def market_closed_alert():
    """Send hourly health check when market is closed."""
    message = f"""
🕒 **Market Closed**  
✅ AI Trader is running  
🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
📡 Waiting for market open...
    """
    send_telegram_message(message.strip())

def market_open_alert(starting_balance: float):
    """Send alert when trading starts."""
    message = f"""
🚀 **Market Open**  
✅ Trading has started  
💼 Starting Balance: ${starting_balance:,.2f}  
🧠 AI Trader is active  
🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    send_telegram_message(message.strip())

def market_close_summary(ending_balance: float, daily_pnl: float, total_trades: int):
    """Send daily summary."""
    message = f"""
📌 **Market Closed - Daily Summary**  
📅 {datetime.now().strftime('%Y-%m-%d')}  
💼 Ending Balance: ${ending_balance:,.2f}  
📈 Daily PnL: ${daily_pnl:,.2f}  
📊 Total Trades: {total_trades}  
✅ AI Trader shutting down for the day  
🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    send_telegram_message(message.strip())
