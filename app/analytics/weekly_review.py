# app/analytics/weekly_review.py

"""
Weekly AI Trading Review
- Loads last 7 days of trades from Cloud Storage
- Calculates PnL, win rate, and performance
- Analyzes news context with FinBERT
- Sends summary to Telegram
"""

import json
import logging
from datetime import datetime, timedelta
from google.cloud import storage
from app.utils.telegram import send_sync
from app.sentiment.finbert import analyze_sentiment

# Set up logging
logging.basicConfig(level=logging.INFO)

# GCS setup
client = storage.Client()
bucket_name = "trading-logs-468901"  # Change to your bucket name
bucket = client.bucket(bucket_name)

def load_weekly_trades():
    """Load trades from the last 7 days."""
    trades = []
    today = datetime.now().date()
    for i in range(7):
        date = today - timedelta(days=i)
        blob_name = f"trades/{date}.jsonl"
        blob = bucket.blob(blob_name)
        if blob.exists():
            try:
                content = blob.download_as_text()
                trades.extend([json.loads(line) for line in content.strip().split("\n") if line])
            except Exception as e:
                logging.error(f"❌ Failed to load {blob_name}: {e}")
    return trades

def generate_weekly_summary():
    """Generate and send weekly trading summary."""
    trades = load_weekly_trades()
    if not trades:
        send_sync("📆 No trades this week.")
        return

    # Calculate stats
    buy_trades = [t for t in trades if t.get("side") == "Buy"]
    sell_trades = [t for t in trades if t.get("side") == "Sell"]
    pnl_values = [t.get("pnl", 0.0) for t in trades]
    total_pnl = sum(pnl_values)
    win_trades = [p for p in pnl_values if p > 0]
    win_rate = (len(win_trades) / len(buy_trades)) * 100 if buy_trades else 0

    # Mock news context (you can enhance with real GNews fetch)
    recent_news = (
        "Fed signals one rate cut in 2025. "
        "Apple reports strong earnings with AI growth. "
        "Oil prices drop due to oversupply concerns."
    )
    sentiment = analyze_sentiment(recent_news)

    # Send summary
    message = f"""
📆 *Weekly Trading Review*  
📅 {datetime.now().strftime('%Y-%m-%d')}  
📊 *Total Trades:* {len(trades)}  
📈 *Buy Trades:* {len(buy_trades)}  
📉 *Sell Trades:* {len(sell_trades)}  
✅ *Win Rate:* {win_rate:.1f}%  
💰 *Net PnL:* ${total_pnl:,.2f}  
🧠 *Market Sentiment:* {sentiment['label']} ({sentiment['score']:.2f})  
🗞️ *Key News:*  
{recent_news}

✅ AI reviewed the week. Ready for next week.
    """.strip()

    send_sync(message)
    logging.info("✅ Weekly review sent to Telegram")

if __name__ == "__main__":
    generate_weekly_summary()
