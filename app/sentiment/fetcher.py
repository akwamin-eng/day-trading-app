# app/sentiment/fetcher.py

"""
Fetches financial news from Alpha Vantage and analyzes sentiment using FinBERT.
Publishes to Pub/Sub.
"""

import requests
import time
import json
from typing import Dict, List
from app.utils.publisher import publish_bar
from app.utils.config import get_config
from app.utils.secrets import get_alphavantage_key
from .finbert import analyze_sentiment

# Load config
config = get_config()
PROJECT_ID = config['gcp']['project_id']
NEWS_TOPIC = config['gcp']['pubsub']['news_data_topic']

# Stocks to monitor
TARGET_SYMBOLS = ["AAPL", "TSLA", "MSFT"]

# Alpha Vantage settings
ALPHA_VANTAGE_KEY = get_alphavantage_key()
NEWS_URL = "https://www.alphavantage.co/query"

# Rate limiting: Free tier = 750 requests per day → ~50/min max, but stay safe
SLEEP_BETWEEN_CALLS = 60  # 1 call per symbol every 60 sec → ~72/hour → ~1,700/day (burst OK, average safe)
MAX_ARTICLES_PER_SYMBOL = 3


def fetch_news(symbol: str) -> List[Dict]:
    """
    Fetch news for a stock from Alpha Vantage.
    """
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": symbol,
        "apikey": ALPHA_VANTAGE_KEY,
        "limit": 5
    }

    try:
        response = requests.get(NEWS_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("feed", [])
        else:
            print(f"❌ Alpha Vantage error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Request failed for {symbol}: {e}")

    return []


def start_news_sentiment_pipeline():
    """
    Main loop: fetch news → analyze sentiment → publish
    """
    print("📰 Starting Alpha Vantage News Pipeline...")
    print("💡 Fetching financial headlines and analyzing with FinBERT...\n")

    while True:
        try:
            for symbol in TARGET_SYMBOLS:
                print(f"🔍 Fetching news for {symbol}...")
                articles = fetch_news(symbol)

                processed = 0
                for article in articles:
                    title = article["title"]

                    # Analyze sentiment with FinBERT (more accurate than AV's label)
                    sentiment = analyze_sentiment(title)
                    print(f"💬 {sentiment['sentiment'].upper()}: {title} | Conf: {sentiment['confidence']:.2f}")

                    # Extract relevance and sentiment from AV
                    av_sentiment = article.get("overall_sentiment_label", "Neutral")
                    av_score = article.get("overall_sentiment_score", 0.0)
                    relevance = article.get("relevance_score", 0.0)
                    topics = article.get("topics", [])

                    # Publish per symbol
                    message = {
                        "symbol": symbol,
                        "headline": title,
                        "summary": article.get("summary", ""),
                        "url": article["url"],
                        "source": article["source"],
                        "publishedAt": article["time_published"],
                        "sentiment": sentiment["sentiment"],
                        "confidence": sentiment["confidence"],
                        "positive": sentiment["positive"],
                        "negative": sentiment["negative"],
                        "neutral": sentiment["neutral"],
                        "alphavantage_sentiment": av_sentiment,
                        "alphavantage_score": round(av_score, 4),
                        "relevance_score": round(relevance, 4),
                        "topics": topics,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    publish_bar(PROJECT_ID, NEWS_TOPIC, message)

                    processed += 1
                    if processed >= MAX_ARTICLES_PER_SYMBOL:
                        break

                # Stay under rate limits
                time.sleep(SLEEP_BETWEEN_CALLS)

        except KeyboardInterrupt:
            print("\n🛑 News pipeline stopped.")
            break
        except Exception as e:
            print(f"❌ Error in news pipeline: {e}")
            time.sleep(60)
