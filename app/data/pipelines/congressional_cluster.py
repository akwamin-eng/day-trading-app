# app/data/pipelines/congressional_cluster.py

"""
Fetch congressional trades from capitoltrades.com
Detect when 2+ Reps buy the same stock → high-conviction signal
"""

import requests
from bs4 import BeautifulSoup
import logging
import json
import os
from datetime import datetime

# Setup
logging.basicConfig(level=logging.INFO)
OUTPUT_FILE = "data/outputs/congress_cluster.json"
URL = "https://www.capitoltrades.com/trades/"


def scrape_congress_trades():
    """Scrape recent trades from capitoltrades.com"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        logging.info("🔍 Scraping capitoltrades.com...")
        resp = requests.get(URL, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.content, 'html.parser')

        trades = []
        # Find all trade rows
        rows = soup.find_all('div', class_='trade-row')

        if not rows:
            logging.warning("⚠️ No trade rows found. Site structure may have changed.")
            return []

        for row in rows[:50]:  # Limit to 50 most recent
            try:
                cols = row.find_all('div', recursive=False)
                if len(cols) >= 6:
                    rep = cols[0].get_text(strip=True)
                    ticker = cols[1].get_text(strip=True)
                    asset = cols[2].get_text(strip=True)
                    trade_type = cols[3].get_text(strip=True)
                    filed = cols[4].get_text(strip=True)
                    traded = cols[5].get_text(strip=True)

                    if trade_type.lower() == "purchase":
                        trades.append({
                            "rep": rep,
                            "ticker": ticker,
                            "type": trade_type,
                            "filed": filed,
                            "traded": traded
                        })
            except Exception as e:
                logging.error(f"❌ Failed to parse row: {e}")
                continue

        logging.info(f"✅ Successfully scraped {len(trades)} trades")
        return trades

    except Exception as e:
        logging.error(f"❌ Failed to scrape capitoltrades.com: {e}")
        return []


def find_clusters(trades, min_reps=2):
    """Find stocks bought by 2+ Reps"""
    from collections import defaultdict
    stock_to_reps = defaultdict(set)

    for trade in trades:
        ticker = trade["ticker"].strip()
        if ticker and ticker != "N/A":
            stock_to_reps[ticker].add(trade["rep"])

    clusters = {k: list(v) for k, v in stock_to_reps.items() if len(v) >= min_reps}
    logging.info(f"🔥 Found {len(clusters)} clustered stocks: {list(clusters.keys())}")
    return clusters


def save_clusters(clusters):
    """Save clusters to file"""
    os.makedirs("data/outputs", exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(clusters, f, indent=2)
    logging.info(f"💾 Saved clusters to {OUTPUT_FILE}")


if __name__ == "__main__":
    logging.info("🧪 Starting Congressional Trade Cluster Engine...")
    trades = scrape_congress_trades()
    clusters = find_clusters(trades, min_reps=2)
    save_clusters(clusters)

    if clusters:
        print("\n🔥 HIGH-CONVICTION CLUSTERS DETECTED:")
        for symbol, reps in clusters.items():
            print(f"  💼 {symbol}: {len(reps)} Reps bought | {', '.join(reps)}")
    else:
        print("\n✅ No clusters found — low consensus today.")
