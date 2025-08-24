# app/data/pipelines/capitol_scraper.py
"""
Scrape political buys from capitoltrades.com
Updated for 2025 React-rendered site
"""
import requests
from bs4 import BeautifulSoup
import logging
import json
import os
import time

logging.basicConfig(level=logging.INFO)
OUTPUT_FILE = "data/outputs/capitol_trades.json"

def get_political_buys():
    url = "https://www.capitoltrades.com/trades/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        logging.info("🧪 Starting Capitol Trades Scraper...")
        time.sleep(1)
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.content, 'html.parser')
        symbols = []

        # Look for stock ticker links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if "/trades/stock/" in href:
                symbol = link.get_text().strip()
                if len(symbol) <= 5 and symbol.isalpha():
                    # Check parent for "Buy"
                    parent = link.find_parent()
                    if parent and ("Buy" in str(parent) or "Purchase" in str(parent)):
                        symbols.append(symbol)

        # Dedupe
        symbols = list(set(symbols))
        logging.info(f"✅ Successfully scraped {len(symbols)} political buys: {symbols}")

        os.makedirs("data/outputs", exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(symbols, f, indent=2)

        return symbols

    except Exception as e:
        logging.error(f"❌ Scraping failed: {e}")
        return []
