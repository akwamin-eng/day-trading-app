# app/data/pipelines/capitol_scraper.py

"""
Scrape recent political trades from capitoltrades.com
Saves to data/outputs/capitol_trades.json
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime

# Setup
logging.basicConfig(level=logging.INFO)
OUTPUT_FILE = "data/outputs/capitol_trades.json"
URL = "https://www.capitoltrades.com/trades/"

def scrape_capitol_trades():
    """Scrape political trades."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        resp = requests.get(URL, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')
        trades = []

        # Updated selector: find all trade rows
        rows = soup.find_all('div', class_='trade-row')
        if not rows:
            # Fallback: look for data in script tags (SPA)
            script = soup.find('script', text=lambda t: t and 'window.__INITIAL_STATE__' in t)
            if script:
                logging.info("📄 Found SPA data in script tag")
                # Extract JSON from script (simplified)
                # In practice, you'd parse __INITIAL_STATE__
                logging.warning("⚠️ SPA parsing not implemented — use API or wait for fix")
                return []

        for row in rows[:20]:  # Limit to 20
            try:
                cols = row.find_all('div')
                if len(cols) >= 5:
                    trade = {
                        "rep": cols[0].get_text(strip=True),
                        "ticker": cols[1].get_text(strip=True),
                        "asset": cols[2].get_text(strip=True),
                        "type": cols[3].get_text(strip=True),
                        "filed": cols[4].get_text(strip=True),
                        "traded": cols[5].get_text(strip=True) if len(cols) > 5 else ""
                    }
                    trades.append(trade)
            except Exception as e:
                logging.error(f"❌ Failed to parse row: {e}")

        # Save to file
        os.makedirs("data/outputs", exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(trades, f, indent=2)

        logging.info(f"✅ Successfully scraped {len(trades)} trades")
        logging.info(f"💾 Saved to {OUTPUT_FILE}")
        return trades

    except Exception as e:
        logging.error(f"❌ Failed to scrape capitoltrades.com: {e}")
        return []

if __name__ == "__main__":
    logging.info("🧪 Starting Capitol Trades Scraper...")
    trades = scrape_capitol_trades()
