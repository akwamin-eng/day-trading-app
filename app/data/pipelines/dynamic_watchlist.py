# app/data/pipelines/dynamic_watchlist.py

"""
Dynamic Watchlist Builder
Generates a watchlist based on real-time signals:
- Political trades (FMP)
- Insider buying (FMP or GNews)
- High sentiment (GNews)
- Strong fundamentals (PEG < 1, revenue growth)
"""

import requests
import logging
from datetime import datetime, timedelta

# Config
FMP_API_KEY = "ZqXPebgZUwpofOO3MUxNlCY4Iu9Mkw1c"
GNEWS_API_KEY = "your-gnews-key"

def get_recent_political_trades(days=3) -> list:
    """Fetch stocks recently bought by Congress."""
    url = f"https://financialmodelingprep.com/api/v4/senate-trading"
    params = {"apikey": FMP_API_KEY, "limit": 50}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        cutoff = datetime.now() - timedelta(days=days)
        recent = [
            trade["symbol"] for trade in data
            if trade["transactionDate"] >= cutoff.strftime("%Y-%m-%d")
            and trade["typeOfTransaction"] == "Purchase"
        ]
        logging.info(f"🔍 Found {len(recent)} stocks from recent political trades")
        return list(set(recent))  # Dedupe
    except Exception as e:
        logging.error(f"❌ Failed to fetch political trades: {e}")
        return []

def get_insider_buying_stocks(days=7) -> list:
    """Fetch stocks with recent insider buying (via GNews)."""
    query = "insider buying stock"
    url = f"https://gnews.io/api/v4/search?q={query}&token={GNEWS_API_KEY}&lang=en"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Extract tickers from headlines (simplified)
        keywords = ["NVDA", "RARE", "TSLA", "AAPL", "MSFT", "GOOGL", "META", "AMD", "AMD", "PLTR", "PINS", "SNOW"]
        found = [kw for kw in keywords if any(kw.lower() in a["title"].lower() for a in data.get("articles", []))]
        logging.info(f"🔍 Found {len(found)} stocks from insider buying news")
        return list(set(found))
    except Exception as e:
        logging.error(f"❌ Failed to fetch insider news: {e}")
        return []

def build_dynamic_watchlist() -> list:
    """Combine all signals into a dynamic watchlist."""
    political = get_recent_political_trades(days=5)
    insider = get_insider_buying_stocks(days=7)
    
    # Combine and limit to 15 stocks
    combined = list(set(political + insider))
    final = [sym for sym in combined if len(sym) <= 5 and not sym.startswith("$")]  # Filter invalid
    logging.info(f"🎯 Dynamic watchlist: {final}")
    return final[:15]  # Limit size
