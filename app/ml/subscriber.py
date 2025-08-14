# app/ml/subscriber.py

"""
ML Merger & Predictor Service
Listens to enriched features and news sentiment,
merges them, runs prediction, and publishes trading signals.
"""

import json
import threading
from datetime import datetime

# Google Cloud
from google.cloud import pubsub_v1

# Local modules
from app.utils.config import get_config
from app.utils.publisher import publish_bar
from app.ml.predictor import predict_signal


# ----------------------------
# Configuration
# ----------------------------

config = get_config()
PROJECT_ID = config['gcp']['project_id']
FEATURES_TOPIC = config['gcp']['pubsub']['enriched_features_topic']
SENTIMENT_TOPIC = config['gcp']['pubsub']['news_data_topic']
OUTPUT_TOPIC = config['gcp']['pubsub']['trading_signals_topic']


# ----------------------------
# Global State: Sentiment Cache
# ----------------------------

# Thread-safe cache for latest sentiment per symbol
_sentiment_cache = {}
_cache_lock = threading.Lock()


# ----------------------------
# Callback: News Sentiment
# ----------------------------

def sentiment_callback(message):
    """
    Called when a new sentiment message is received.
    Stores it in a thread-safe cache for merging.
    """
    try:
        data = json.loads(message.data.decode("utf-8"))
        symbol = data['symbol']

        # Update cache
        with _cache_lock:
            _sentiment_cache[symbol] = {
                'sentiment': data.get('sentiment', 'neutral'),
                'confidence': data.get('confidence', 0.0),
                'alphavantage_score': data.get('alphavantage_score', 0.0)
            }

        print(f"📰 Cached sentiment for {symbol}: {data['sentiment']} | Conf: {data['confidence']:.2f}")
        message.ack()

    except Exception as e:
        print(f"❌ Error processing sentiment message: {e}")
        message.nack()  # Re-deliver


# ----------------------------
# Callback: Enriched Features
# ----------------------------

def features_callback(message):
    """
    Called when a new technical feature message is received.
    Merges with latest sentiment and runs prediction.
    """
    try:
        data = json.loads(message.data.decode("utf-8"))
        symbol = data['symbol']
        timestamp = data['timestamp']

        # Get latest sentiment (thread-safe)
        with _cache_lock:
            sentiment = _sentiment_cache.get(symbol)

        # Build merged feature vector
        merged = {
            "symbol": symbol,
            "timestamp": timestamp,
            "price": data['price'],
            "sma_short": data['sma_short'],
            "sma_medium": data['sma_medium'],
            "sma_long": data['sma_long'],
            "rsi": data['rsi'],
            "bb_percent_b": data['bb_percent_b'],
            "momentum": data['momentum'],
            "atr": data['atr'],
            "volume_ratio": data['volume_ratio'],
            "sentiment_score": 0.0  # Default if no sentiment
        }

        # Compute combined sentiment score
        if sentiment:
            base_score = sentiment['confidence']
            av_score = sentiment.get('alphavantage_score', 0.0)
            if sentiment['sentiment'] == 'positive':
                combined = (base_score + av_score) / 2
            elif sentiment['sentiment'] == 'negative':
                combined = - (base_score + av_score) / 2
            else:
                combined = 0.0
            merged['sentiment_score'] = round(combined, 4)

        # Run prediction and publish signal
        predict_signal(merged)

        # Acknowledge message
        message.ack()

    except Exception as e:
        print(f"❌ Error in features_callback: {e}")
        message.nack()


# ----------------------------
# Main: Start ML Merger
# ----------------------------

def start_ml_merger():
    """
    Starts subscribers for both topics.
    Blocks until interrupted.
    """
    subscriber = pubsub_v1.SubscriberClient()

    # Subscription paths
    features_sub_path = subscriber.subscription_path(PROJECT_ID, "enriched-features-sub")
    sentiment_sub_path = subscriber.subscription_path(PROJECT_ID, "news-sentiment-sub")

    print("🧠 ML Prediction Engine Starting...")
    print(f"  📊 Listening to: {FEATURES_TOPIC}")
    print(f"  📰 Listening to: {SENTIMENT_TOPIC}")
    print(f"  🎯 Publishing signals to: {OUTPUT_TOPIC}")
    print(f"  🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💡 Waiting for first messages...\n")

    # Subscribe to both topics
    streaming_pull_future1 = subscriber.subscribe(sentiment_sub_path, callback=sentiment_callback)
    streaming_pull_future2 = subscriber.subscribe(features_sub_path, callback=features_callback)

    try:
        # Keep both streams alive
        streaming_pull_future1.result()
        streaming_pull_future2.result()
    except KeyboardInterrupt:
        print("\n🛑 ML merger stopped by user.")
    except Exception as e:
        print(f"❌ Subscriber error: {e}")
    finally:
        subscriber.close()
        print("✅ Subscriber shutdown complete.")


# ----------------------------
# Run as Standalone (Optional)
# ----------------------------

if __name__ == "__main__":
    start_ml_merger()
