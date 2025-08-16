# app/data/pipelines/gnews_insider.py

import requests
import logging
import json
from datetime import datetime
import os  # ✅ Add this line

API_KEY = "c026fd5200d848066e95943e8f40754b"
BASE_URL = "https://gnews.io/api/v4/search"

def search_insider_news(query="insider buying"):
    params = {
        "q": query,
        "token": API_KEY,
        "lang": "en",
        "country": "us",
        "max": 10
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        data = resp.json()
        if data.get("code") == "invalid_token":
            logging.error("❌ GNews: Invalid API key")
            return None
        data["retrieved_at"] = datetime.utcnow().isoformat()
        return data
    except Exception as e:
        logging.error(f"❌ GNews request failed: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🧪 Testing GNews: Insider Buying News")
    results = search_insider_news()  # ✅ Correct function name
    if results:
        articles = results.get("articles", [])
        print(f"✅ Found {len(articles)} articles")
        os.makedirs("data/outputs", exist_ok=True)
        with open("data/outputs/gnews_insider.json", "w") as f:
            json.dump(results, f, indent=2)
        print("💾 Saved to data/outputs/gnews_insider.json")
    else:
        print("❌ No results or error")
