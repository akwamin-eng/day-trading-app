# app/analysis/market_regime.py

"""
Market Regime Detection Engine (FMP v3)
Uses: https://financialmodelingprep.com/api/v3/historical-price-full/SPY
No yfinance, no pandas ambiguity, no NumPy 2.x issues.
"""

import requests
import logging
from typing import Literal

# Set up logging
logging.basicConfig(level=logging.INFO)

# FMP API
FMP_API_KEY = "ZqXPebgZUwpofOO3MUxNlCY4Iu9Mkw1c"
URL = "https://financialmodelingprep.com/api/v3/historical-price-full/SPY"


def compute_rsi(prices: list, window: int = 14) -> float:
    """Compute RSI from a list of prices."""
    if len(prices) < window + 1:
        return 50.0  # Neutral

    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[:window]) / window
    avg_loss = sum(losses[:window]) / window

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def detect_regime(prices: list, sma_window: int = 50) -> Literal["bull", "bear", "neutral"]:
    """
    Detect market regime from price list.
    Returns "bull", "bear", or "neutral".
    """
    if len(prices) < 20:
        logging.warning("⚠️ Not enough data for regime detection.")
        return "neutral"

    current_price = prices[-1]
    sma = sum(prices[-sma_window:]) / sma_window
    rsi = compute_rsi(prices, window=14)

    if current_price > sma and rsi > 50:
        return "bull"
    elif current_price < sma and rsi < 40:
        return "bear"
    else:
        return "neutral"


def detect_regime_by_symbol(symbol: str = "SPY") -> Literal["bull", "bear", "neutral"]:
    """Fetch SPY data and detect regime."""
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
    params = {"apikey": FMP_API_KEY}
    logging.info(f"🔍 Fetching market data: {url}")

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if "historical" not in data or len(data["historical"]) < 50:
            logging.warning("⚠️ Not enough data from FMP.")
            return "neutral"

        prices = [day["close"] for day in data["historical"]]
        return detect_regime(prices)

    except Exception as e:
        logging.error(f"❌ Failed to detect regime: {e}")
        return "neutral"


# === Main Execution (for testing) ===
if __name__ == "__main__":
    print("🧪 Testing Market Regime Detection...")
    regime = detect_regime_by_symbol("SPY")
    print(f"🎯 Current Market Regime: {regime.upper()}")
