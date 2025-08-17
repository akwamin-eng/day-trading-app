# app/signals/fusion.py

"""
Signal Fusion Engine
Combines political, sentiment, fundamental, and technical signals
Uses self-learned weights to boost high-performing signals.
All data from FMP, GNews, Alpha Vantage — no yfinance.
"""

import json
import requests
import logging
from typing import Dict, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)

# === CONFIGURATION ===
FMP_API_KEY = "ZqXPebgZUwpofOO3MUxNlCY4Iu9Mkw1c"
FMP_TECHNICAL_URL = "https://financialmodelingprep.com/api/v3/technical_indicator/daily/{symbol}"
FMP_HISTORICAL_URL = "https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
ALPHA_VANTAGE_API_KEY = "RN4AW0736R8L9T17"
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

# Paths
WEIGHTS_FILE = "trading_logs/signal_weights.json"
DEFAULT_WEIGHTS = {
    "political": 1.0,
    "sentiment": 1.0,
    "fundamentals": 1.0,
    "technical": 1.0
}


def load_weights() -> Dict[str, float]:
    """Load learned signal weights."""
    try:
        with open(WEIGHTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"⚠️ Could not load weights: {e}. Using defaults.")
        return DEFAULT_WEIGHTS.copy()


def get_technical_signal(symbol: str) -> str:
    """Fetch RSI and Bollinger Bands from FMP."""
    url = FMP_TECHNICAL_URL.format(symbol=symbol)
    params = {"period": 14, "type": "rsi,bb", "apikey": FMP_API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data or len(data) < 2:
            return "neutral"
        latest = data[0]
        rsi = latest.get("rsi")
        lower_bb = latest.get("lowerBB")
        upper_bb = latest.get("upperBB")
        close = latest.get("close")
        if not all([rsi, lower_bb, upper_bb, close]):
            return "neutral"
        if close < lower_bb and rsi < 30:
            return "buy"
        elif close > upper_bb and rsi > 70:
            return "sell"
        return "neutral"
    except Exception as e:
        logging.error(f"❌ FMP technical fetch failed for {symbol}: {e}")
        return "neutral"


def get_fundamentals(symbol: str) -> Optional[Dict]:
    """Fetch company fundamentals from Alpha Vantage."""
    params = {
        "function": "OVERVIEW",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY
    }
    try:
        resp = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=10)
        data = resp.json()
        if "Note" in data:
            logging.error("❌ Rate limit reached.")
            return None
        if "Error Message" in data:
            logging.error(f"❌ {data['Error Message']}")
            return None
        return data
    except Exception as e:
        logging.error(f"❌ Failed to fetch fundamentals: {e}")
        return None


def get_market_regime() -> str:
    """Detect bull/bear/neutral using SPY data from FMP."""
    url = FMP_HISTORICAL_URL.format(symbol="SPY")
    params = {"apikey": FMP_API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "historical" not in data or len(data["historical"]) < 50:
            return "neutral"
        prices = [day["close"] for day in data["historical"]]
        current_price = prices[-1]
        sma = sum(prices[-50:]) / 50
        # Simplified RSI
        gains = sum(max(0, prices[i] - prices[i-1]) for i in range(-14, 0))
        losses = sum(max(0, prices[i-1] - prices[i]) for i in range(-14, 0))
        avg_gain = gains / 14
        avg_loss = losses / 14
        rs = avg_gain / avg_loss if avg_loss != 0 else 100
        rsi = 100 - (100 / (1 + rs))
        if current_price > sma and rsi > 50:
            return "bull"
        elif current_price < sma and rsi < 40:
            return "bear"
        return "neutral"
    except Exception as e:
        logging.error(f"❌ Failed to detect regime: {e}")
        return "neutral"


def generate_fused_signal(symbol: str, political_buy: bool = False):
    """Generate a fused signal using all data sources and learned weights."""
    logging.info(f"🔍 Evaluating {symbol} | Political Buy: {political_buy}")
    
    weights = load_weights()
    total_score = 0.0
    reasons = []

    # 1. Political Signal
    if political_buy:
        total_score += 1.0 * weights["political"]
        reasons.append("Rep bought")
    else:
        logging.info(f"❌ No political buy for {symbol}")

    # 2. Sentiment (simulated — replace with real FinBERT later)
    sentiment_score = 0.7  # Simulated positive sentiment
    if sentiment_score > 0.5:
        total_score += 1.0 * weights["sentiment"]
        reasons.append(f"Sentiment: {sentiment_score:.2f}")
    else:
        logging.info(f"❌ Negative sentiment for {symbol}")

    # 3. Fundamentals
    fundamentals = get_fundamentals(symbol)
    peg_ratio = float(fundamentals.get("PEGRatio", 999)) if fundamentals else 999
    if fundamentals and peg_ratio < 1.0:
        total_score += 1.0 * weights["fundamentals"]
        reasons.append(f"PEG: {peg_ratio:.2f}")
    else:
        logging.info(f"❌ Weak fundamentals for {symbol}")

    # 4. Technical Signal
    tech_signal = get_technical_signal(symbol)
    if tech_signal == "buy":
        total_score += 1.0 * weights["technical"]
        reasons.append("RSI < 30 & price near lower Bollinger")
    elif tech_signal == "sell":
        logging.info(f"❌ Technical sell signal for {symbol}")
        return None
    else:
        logging.info(f"❌ Neutral technical signal for {symbol}")

    # 5. Market Regime
    regime = get_market_regime()
    if regime == "bear":
        total_score *= 0.5  # Reduce confidence in bear market
        logging.info(f"📉 Market regime: {regime.upper()} → reducing signal strength")
    else:
        logging.info(f"📈 Market regime: {regime.upper()} → normal confidence")

    # Final Decision
    if total_score >= 2.5:
        confidence = min(total_score / 4.0, 1.0)
        logging.info(f"✅ High-conviction signal for {symbol} (Score: {total_score:.2f}, Confidence: {confidence:.2f})")
        return {
            "symbol": symbol,
            "action": "buy",
            "confidence": confidence,
            "reason": ", ".join(reasons),
            "regime": regime
        }
    else:
        logging.info(f"❌ Total score {total_score:.2f} < 2.5 → no signal for {symbol}")
        return None


def execute_paper_trade(signal: Dict):
    """Execute a paper trade based on fused signal."""
    try:
        # Simulate position size (replace with real logic later)
        qty = int(100 * signal["confidence"])  # Example: 75 shares at 0.75 confidence
        if qty == 0:
            logging.info("❌ Position size is 0 — skipping trade")
            return

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
        print(f"📢 Telegram Alert: {message}")

    except Exception as e:
        logging.error(f"❌ Trade failed: {e}")
        print(f"🚨 Trade Failed: {e}")
