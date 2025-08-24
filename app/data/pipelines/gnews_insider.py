# app/data/pipelines/gnews_insider.py
"""
Find stocks with 'insider buying' news
"""
from gnews import GNews
import logging

logging.basicConfig(level=logging.INFO)

def get_insider_news():
    google_news = GNews(language='en', country='US', period='7d', max_results=10)
    try:
        news = google_news.get_news("insider buying OR stock purchase OR CEO buys")
        logging.info(f"🔍 Found {len(news)} insider-related articles")

        # Expanded keyword map
        ticker_map = {
            "RARE": ["rare earth", "rare hospitality", "rare stock", "rare"],
            "NVDA": ["nvidia", "jensen huang", "ai chip", "geforce", "data center"],
            "TSLA": ["tesla", "elon musk", "cybertruck", "ai day", "fremont"],
            "AMD": ["amd", "lisa su", "ryzen", "epyc", "chip"],
            "GME": ["gamestop", "ryan cohen", "rc ventures", "meme stock"],
            "AMC": ["amc", "adam aron", "meme stock", "theater"],
            "SPY": ["s&p 500", "spdr", "index fund"]
        }

        results = {}
        for article in news:
            title = article['title'].lower()
            for ticker, keywords in ticker_map.items():
                if any(k in title for k in keywords):
                    results[ticker] = "positive"
                    logging.info(f"🎯 Matched {ticker} in: {title}")

        logging.info(f"✅ Insider news signals: {results}")
        return results

    except Exception as e:
        logging.error(f"❌ GNews error: {e}")
        return {}
