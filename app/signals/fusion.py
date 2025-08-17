# app/signals/fusion.py

"""
Signal Fusion Engine
Combines political, sentiment, fundamental, and technical signals
Uses self-learned weights to boost high-performing signals.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from app.utils.secrets import get_paper_api_key, get_paper_secret_key
from alpaca.trading.client import TradingClient
from app.risk.position import get_position_size
from app.utils.telegram_alerts import send_sync
from app.sentiment.finbert import analyze_sentiment
from app.analysis.market_regime import detect_regime
from pandas_ta import rsi, sma, bbands
import yfinance as yf

# Set up logging
logging.basicConfig(level=logging.INFO)

# Paths
WEIGHTS_FILE = "trading_logs/signal_weights.json"
DEFAULT_WEIGHTS = {
    "political": 1.0,
    "sentiment": 1.0,
    "fundamentals": 1.0,
    "technical": 1.0
}

# Initialize Alpaca
client = TradingClient(get_paper_api_key(), get_paper_secret_key(), paper=True)


def load_weights() -> Dict[str, float]:
    """Load learned signal weights."""
    try:
        with open(WEIGHTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"⚠️ Could not load weights: {e}. Using defaults.")
        return DEFAULT_WEIGHTS.copy()


def get_technical_signal(symbol: str) -> str:
    """Generate RSI + Bollinger signal."""
    df = yf.download(symbol, period="1mo", interval="1d")
    if df.empty:
        return "neutral"
    rsi_val = rsi(df["Close"]).iloc[-1]
    upper, mid, lower = bbands(df["Close"])
    price = df["Close"].iloc[-1]
    if rsi_val < 30 and price < lower.iloc[-1]:
        return "buy"
    elif rsi_val > 70 and price > upper.iloc[-1]:
        return "sell"
    return "neutral"


def generate_fused_signal(symbol: str, political_buy: bool = False):
    """
    Generate a fused signal using all data sources and learned weights.
    """
    weights = load_weights()
    total_score = 0.0
    reasons = []

    # 1. Political Signal
    if political_buy:
        total_score += 1.0 * weights["political"]
        reasons.append("Rep bought")
    else:
        logging.info(f"❌ No political buy for {symbol}")

    # 2. Sentiment Signal
    news = f"{symbol} stock news"
    sentiment = analyze_sentiment(news)
    if sentiment["label"] == "Positive":
        total_score += 1.0 * weights["sentiment"]
        reasons.append(f"Sentiment: {sentiment['score']:.2f}")
    elif sentiment["label"] == "Negative":
        logging.info(f"❌ Negative sentiment for {symbol}")
        return None

    # 3. Fundamental Signal
    try:
        stock = yf.Ticker(symbol)
        pe = stock.info.get("trailingPE", 100)
        if pe < 30:
            total_score += 1.0 * weights["fundamentals"]
            reasons.append(f"P/E: {pe:.1f}")
    except:
        pass

    # 4. Technical Signal
    tech_signal = get_technical_signal(symbol)
    if tech_signal == "buy":
        total_score += 1.0 * weights["technical"]
        reasons.append("RSI < 30 & price near lower Bollinger")
    elif tech_signal == "sell":
        logging.info(f"❌ Technical sell signal for {symbol}")
        return None

    # 5. Market Regime
    prices = yf.download("SPY", period="6mo")["Close"]
    regime = detect_regime(prices)
    if regime == "bear":
        total_score *= 0.5  # Reduce confidence in bear market

    # Final Decision
    if total_score >= 2.5:
        return {
            "symbol": symbol,
            "action": "buy",
            "confidence": min(total_score / 4.0, 1.0),
            "reason": ", ".join(reasons),
            "regime": regime
        }
    return None


def execute_paper_trade(signal: Dict):
    """Execute a paper trade based on fused signal."""
    try:
        qty = get_position_size(signal["symbol"])
        if qty == 0:
            logging.info("❌ Position size is 0 — skipping trade")
            return

        order = client.submit_order(
            symbol=signal["symbol"],
            qty=qty,
            side="buy",
            type="market",
            time_in_force="day"
        )
        logging.info(f"✅ Paper trade executed: Buy {qty} shares of {signal['symbol']}")

        # Send Telegram alert
        message = f"""
🎯 **High-Conviction Buy Signal**
📊 {signal['symbol']} (Confidence: {signal['confidence']:.2f})
💡 {signal['reason']}
🌍 Market: {signal['regime'].upper()}
📝 Paper trade executed
🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """.strip()
        send_sync(message)

    except Exception as e:
        logging.error(f"❌ Trade failed: {e}")
        send_sync(f"🚨 Trade Failed: {e}")


# === Main Execution (for testing) ===
if __name__ == "__main__":
    print("🧪 Testing Fused Signal Engine...")
    signal = generate_fused_signal("RARE", political_buy=True)
    if signal:
        print(f"✅ Signal: {signal}")
        execute_paper_trade(signal)
    else:
        print("❌ No signal generated")
