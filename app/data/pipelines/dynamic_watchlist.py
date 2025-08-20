# app/data/pipelines/dynamic_watchlist.py

"""
Dynamic Watchlist Engine
- Tries FMP first
- Falls back to static list if rate-limited
"""

import requests
import logging
import json
import os
import time

# Setup
logging.basicConfig(level=logging.INFO)
WATCHLIST_FILE = "data/outputs/dynamic_watchlist.json"
FMP_API_KEY = "ZqXPebgZUwpofOO3MUxNlCY4Iu9Mkw1c"

# FMP Endpoints
GAINERS_URL = "https://financialmodelingprep.com/api/v3/gainers"
SCREENER_URL = "https://financialmodelingprep.com/api/v3/stock-screener"


def fetch_with_retry(url, params, retries=2):
    """Fetch with retry and delay"""
    for i in range(retries + 1):
        try:
            time.sleep(1)  # Rate limit: 1 req/sec
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 429:
                wait = 60 * (i + 1)
                logging.warning(f"⚠️ Rate limit hit. Waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if i == retries:
                logging.error(f"❌ Failed after {retries+1} attempts: {e}")
                return None
            time.sleep(2 * (i + 1))
    return None


def get_top_gainers(limit=20):
    """Try to get top gainers from FMP"""
    params = {"apikey": FMP_API_KEY}
    data = fetch_with_retry(GAINERS_URL, params)
    if not data:
        return []
    symbols = []
    for item in data:
        symbol = item.get("symbol", "")
        if symbol and "." not in symbol:
            symbols.append(symbol)
    return symbols[:limit]


def screen_stocks():
    """Try to screen stocks from FMP"""
    params = {
        "apikey": FMP_API_KEY,
        "marketCapMoreThan": 1000000000,
        "volumeMoreThan": 500000,
        "isActivelyTrading": "true",
        "limit": 100
    }
    data = fetch_with_retry(SCREENER_URL, params)
    if not data:
        return []
    symbols = []
    for item in data:
        symbol = item.get("symbol", "")
        if symbol and "." not in symbol:
            symbols.append(symbol)
    return symbols


def build_dynamic_watchlist():
    """Build watchlist with fallback"""
    logging.info("🔍 Building dynamic watchlist...")

    # Try live data
    gainers = get_top_gainers()
    screened = screen_stocks()
    combined = list(set(gainers + screened))

    # Fallback if API fails
    if not combined:
        logging.warning("⚠️ FMP rate-limited → using fallback watchlist")
        combined = ["RARE", "NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "META", "AMD", "INTC", "PINS"]

    # Dedupe and limit
    final_list = combined[:20]

    # Save
    os.makedirs("data/outputs", exist_ok=True)
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(final_list, f, indent=2)

    logging.info(f"✅ Dynamic watchlist built: {final_list}")
    logging.info(f"💾 Saved to {WATCHLIST_FILE}")

    return final_list


if __name__ == "__main__":
    watchlist = build_dynamic_watchlist()
    print("\n🎯 Dynamic Watchlist:")
    for i, symbol in enumerate(watchlist, 1):
        print(f"  {i}. {symbol}")
