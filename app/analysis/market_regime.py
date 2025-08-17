# app/analysis/market_regime.py

"""
Market Regime Detection Engine (FMP v3 Version)
Uses: https://financialmodelingprep.com/api/v3/historical-price-full/SPY
No yfinance, no pandas ambiguity, no 404 errors.
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


def detect_regime_by_symbol(symbol: str = "SPY") -> Literal["bull", "bear", "neutral"]:
    """
    Detect market regime using FMP v3 API.
    """
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
    params = {"apikey": FMP_API_KEY}
    logging.info(f"🔍 Fetching market data from FMP v3: {url}")

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if "historical" not in data or len(data["historical"]) < 20:
            logging.warning("⚠️ Not enough data from FMP.")
            return "neutral"

        # Extract closing prices
        prices = [day["close"] for day in data["historical"]]
        current_price = prices[-1]

        # Calculate SMA (use 50-day or half the data if less)
        sma_window = min(50, len(prices) // 2)
        sma = sum(prices[-sma_window:]) / sma_window

        # Compute RSI
        rsi = compute_rsi(prices, window=14)

        # Detect regime
        if current_price > sma and rsi > 50:
            regime = "bull"
        elif current_price < sma and rsi < 40:
            regime = "bear"
        else:
            regime = "neutral"

        logging.info(f"📊 Market Regime: {regime.upper()} | Price: ${current_price:.2f} | "
                     f"SMA{sma_window}: ${sma:.2f} | RSI: {rsi:.2f}")

        return regime

    except Exception as e:
        logging.error(f"❌ Failed to detect regime: {e}")
        return "neutral"


# === Main Execution (for testing) ===
if __name__ == "__main__":
    print("🧪 Testing Market Regime Detection (FMP v3)...")
    regime = detect_regime_by_symbol("SPY")
    print(f"🎯 Current Market Regime: {regime.upper()}")
