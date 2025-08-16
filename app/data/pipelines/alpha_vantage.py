# app/data/pipelines/alpha_vantage.py

import requests
import logging
import json
from datetime import datetime
import os

API_KEY = "RN4AW0736R8L9T17"
BASE_URL = "https://www.alphavantage.co/query"

def fetch_stock_overview(symbol="AAPL"):
    """Fetch company overview (free endpoint)."""
    params = {
        "function": "OVERVIEW",
        "symbol": symbol,
        "apikey": API_KEY
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        data = resp.json()
        if "Note" in data:
            logging.error(f"⚠️ Alpha Vantage rate limit: {data['Note']}")
            return None
        if "Error Message" in data:
            logging.error(f"❌ {data['Error Message']}")
            return None
        data["fetched_at"] = datetime.utcnow().isoformat()
        return data
    except Exception as e:
        logging.error(f"❌ Request failed: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🧪 Testing Alpha Vantage: Company Overview")
    data = fetch_stock_overview("AAPL")
    if data:
        print(f"✅ Got data for {data.get('Name')}")
        os.makedirs("data/outputs", exist_ok=True)
        with open("data/outputs/alpha_vantage.json", "w") as f:
            json.dump(data, f, indent=2)
        print("💾 Saved to data/outputs/alpha_vantage.json")
    else:
        print("❌ No data returned")
