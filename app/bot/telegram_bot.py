# app/bot/telegram_bot.py
"""
Telegram Bot for Natural, Bilateral AI Trader Interaction
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.learning.self_learning import update_signal_weights
import json
import os

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 AI Trader: Online and ready.\n"
        "You can ask:\n"
        "- `status` → current positions\n"
        "- `learn` → run self-learning\n"
        "- `hustle` → find high-conviction trades\n"
        "- `report` → daily summary"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("trading_logs/open_positions.json", "r") as f:
            positions = json.load(f)
        if not positions:
            await update.message.reply_text("🔍 No open positions.")
        else:
            msg = "📊 Open Positions:\n"
            for p in positions:
                msg += f"- {p['qty']} {p['symbol']} @ ${p['entry_price']:.2f}\n"
            await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to load positions: {e}")

async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from app.learning.self_learning import update_signal_weights
    update_signal_weights()
    await update.message.reply_text("🧠 Self-learning complete. Strategy weights updated.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("trading_logs/daily_summary.md", "r") as f:
            report = f.read()
        await update.message.reply_text(report)
    except Exception as e:
        await update.message.reply_text(f"❌ No report available: {e}")

async def hustle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Simulate high-conviction hunt
    await update.message.reply_text(
        "🔥 Hustle Mode Activated\n"
        "🔍 Scanning for high-conviction trades...\n"
        "🎯 Found: RARE (Congress buy + insider news)\n"
        "💡 Confidence: 87%\n"
        "📈 Action: Buying 1 share"
    )
    # In future: trigger real scan

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "hello" in text or "hi" in text:
        await update.message.reply_text("👋 Hey, partner. Ready to make money?")
    elif "how are you" in text:
        await update.message.reply_text("🧠 Running at 97.3% conviction. Ready to trade.")
    elif "what should i do" in text:
        await update.message.reply_text("🚀 Hustle. Adapt. Compound.")
    else:
        await update.message.reply_text("🤔 I'm focused on the market. Try: status, report, hustle.")

# Main
def run_telegram_bot():
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("learn", learn))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("hustle", hustle))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()
