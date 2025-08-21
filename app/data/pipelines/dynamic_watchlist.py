# app/data/pipelines/dynamic_watchlist.py

import requests
import logging
import json
import os
import time

logging.basicConfig(level=logging.INFO)
WATCHLIST_FILE = "data/outputs/dynamic_watchlist.json"
FMP_API_KEY = "ZqXPebgZUwpofOO3MUxNlCY4Iu9Mkw1c"

GAINERS_URL = "https://financialmodelingprep.com/api/v3/gainers"
SCREENER_URL = "https://financialmodelingprep.com/api/v3/stock-screener"
PROFILE_URL = "https://financialmodelingprep.com/api/v3/profile/{symbol}"


def fetch_with_retry(url, params, retries=2):
    for i in range(retries + 1):
        try:
            time.sleep(1)
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
                logging.error(f"❌ Failed: {e}")
                return None
            time.sleep(2 * (i + 1))
    return None


def get_top_gainers(limit=20):
    data = fetch_with_retry(GAINERS_URL, {"apikey": FMP_API_KEY})
    if not 
        return []
    return [item["symbol"] for item in data if "." not in item.get("symbol", "")][:limit]


def screen_stocks():
    params = {
        "apikey": FMP_API_KEY,
        "marketCapMoreThan": 1000000000,
        "volumeMoreThan": 500000,
        "isActivelyTrading": "true",
        "limit": 100
    }
    data = fetch_with_retry(SCREENER_URL, params)
    if not 
        return []
    return [item["symbol"] for item in data if "." not in item.get("symbol", "")]


def build_dynamic_watchlist():
    logging.info("🔍 Building dynamic watchlist...")
    gainers = get_top_gainers()
    screened = screen_stocks()
    combined = list(set(gainers + screened))
    if not combined:
        logging.warning("⚠️ FMP rate-limited → using fallback")
        combined = ["RARE", "NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "META", "AMD"]
    final_list = combined[:20]
    os.makedirs("data/outputs", exist_ok=True)
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(final_list, f, indent=2)
    logging.info(f"✅ Dynamic watchlist built: {final_list}")
    return final_list


if __name__ == "__main__":
    build_dynamic_watchlist()
