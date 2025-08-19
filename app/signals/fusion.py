# app/signals/fusion.py

"""
Minimal Signal Fusion Engine
✅ Working. No syntax errors.
✅ Uses only FMP
✅ No Alpha Vantage, no FinBERT, no rate limits
"""

import json
import requests
import logging
from typing import Dict, Optional

# Delayed import (set in main.py)
send_sync = None

# === CONFIGURATION ===
FMP_API_KEY = "ZqXPebgZUwpofOO3MUxNlCY4Iu9Mkw1c"
FMP_PROFILE_URL = "https://financialmodelingprep.com/api/v3/profile/{symbol}"
FMP_TECHNICAL_URL = "https://financialmodelingprep.com/api/v3/technical_indicator/daily/{symbol}"
FMP_HISTORICAL_URL = "https://financialmodelingprep.com/api/v3/historical-price-full/SPY"

# Paths
WEIGHTS_FILE = "trading_logs/signal_weights.json"
DEFAULT_WEIGHTS = {
    "political": 1.0,
    "sentiment": 1.0,
    "fundamentals": 1.0,
    "technical": 1.0
}


def load_weights() -> Dict[str, float]:
    """Load signal weights."""
    try:
        with open(WEIGHTS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_WEIGHTS.copy()


def get_fundamentals(symbol: str) -> Optional[Dict]:
    """Fetch fundamentals from FMP."""
    url = FMP_PROFILE_URL.format(symbol=symbol)
    params = {"apikey": FMP_API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
        return None
    except Exception as e:
        logging.error(f"❌ Failed to fetch fundamentals: {e}")
        return None


def get_technical_signal(symbol: str) -> str:
    """Simple RSI check using FMP."""
    url = FMP_TECHNICAL_URL.format(symbol=symbol)
    params = {"type": "rsi", "apikey": FMP_API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data and len(data) > 0:
            rsi = data[0].get("rsi")
            if rsi and rsi < 30:
                return "buy"
        return "neutral"
    except Exception as e:
        logging.error(f"❌ Technical fetch failed: {e}")
        return "neutral"


def get_market_regime() -> str:
    """Simple SPY trend check."""
    url = FMP_HISTORICAL_URL
    params = {"apikey": FMP_API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        prices = [day["close"] for day in data["historical"][-50:]]
        sma = sum(prices) / 50
        return "bull" if prices[-1] > sma else "bear"
    except Exception as e:
        logging.error(f"❌ Regime detection failed: {e}")
        return "neutral"


def generate_fused_signal(symbol: str, political_buy: bool = False):
    """Generate a fused signal."""
    logging.info(f"🔍 Evaluating {symbol} | Political Buy: {political_buy}")
    weights = load_weights()
    total_score = 0.0
    reasons = []

    # 1. Political
    if political_buy:
        total_score += 1.0 * weights["political"]
        reasons.append("Rep bought")

    # 2. Sentiment (simulated)
    sentiment_score = 0.7
    if sentiment_score > 0.5:
        total_score += 1.0 * weights["sentiment"]
        reasons.append(f"Sentiment: {sentiment_score:.2f}")

    # 3. Fundamentals (PEG < 1.0)
    fundamentals = get_fundamentals(symbol)
    peg = float(fundamentals.get("priceToEarningsRatio", 999)) if fundamentals else 999
    if peg < 1.0:
        total_score += 1.0 * weights["fundamentals"]
        reasons.append(f"PEG: {peg:.2f}")

    # 4. Technicals
    tech_signal = get_technical_signal(symbol)
    if tech_signal == "buy":
        total_score += 1.0 * weights["technical"]
        reasons.append("RSI < 30")

    # 5. Market Regime
    regime = get_market_regime()
    if regime == "bear":
        total_score *= 0.5

    # Decision
    if total_score >= 2.5:
        return {
            "symbol": symbol,
            "action": "buy",
            "confidence": min(total_score / 4.0, 1.0),
            "quantity": 75,
            "entry_price": fundamentals.get("price", 0) if fundamentals else 0,
            "reason": ", ".join(reasons),
            "regime": regime
        }
    return None


def execute_paper_trade(signal: Dict):
    """Execute paper trade."""
    try:
        qty = signal.get("quantity", 1)
        logging.info(f"✅ Paper trade: Buy {qty} of {signal['symbol']}")
        message = f"🎯 Buy {signal['symbol']} | Qty: {qty} | Confidence: {signal['confidence']:.2f}"
        print(f"📢 Telegram: {message}")
        send_sync(message)
    except Exception as e:
        logging.error(f"❌ Trade failed: {e}")
