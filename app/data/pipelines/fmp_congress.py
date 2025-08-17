# app/data/pipelines/fmp_congress.py

"""
FMP Congressional Trading Pipeline (House Only - Stable)
Uses: https://financialmodelingprep.com/stable/house-latest
Free-tier compatible.
"""

import requests
import logging
import json
from datetime import datetime
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

FMP_API_KEY = "ZqXPebgZUwpofOO3MUxNlCY4Iu9Mkw1c"
HOUSE_URL = "https://financialmodelingprep.com/stable/house-latest"


def fetch_house_trades():
    """Fetch recent House financial disclosures."""
    logging.info("🔍 Fetching House trades from FMP")
    try:
        resp = requests.get(HOUSE_URL, params={"apikey": FMP_API_KEY}, timeout=10)
        if resp.status_code == 403:
            logging.error("❌ 403: Access denied. Check API key or whitelisting.")
            return []
        elif resp.status_code == 404:
            logging.error("❌ 404: Endpoint not found. Check FMP docs.")
            return []
        elif resp.status_code != 200:
            logging.error(f"❌ HTTP {resp.status_code}: {resp.text[:100]}")
            return []

        data = resp.json()
        logging.info(f"✅ Fetched {len(data)} House trades")
        return data
    except Exception as e:
        logging.error(f"❌ Request failed: {e}")
        return []


# === Main Execution ===
if __name__ == "__main__":
    print("🧪 Testing FMP Congressional Trading (House Only)...")
    os.makedirs("data/outputs", exist_ok=True)

    trades = fetch_house_trades()

    # Add metadata
    output_data = {
        "trades": trades,
        "source": "fmp_house_latest",
        "fetched_at": datetime.utcnow().isoformat()
    }

    output_file = "data/outputs/fmp_congress.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"💾 Saved {len(trades)} House trades to {output_file}")
