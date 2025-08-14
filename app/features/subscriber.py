# app/features/subscriber.py

"""
Pub/Sub subscriber that computes real-time features from market data.
"""

from google.cloud import pubsub_v1
from app.utils.config import get_config
from app.utils.publisher import publish_bar
import json
import time

# Load config
config = get_config()
PROJECT_ID = config['gcp']['project_id']
INPUT_TOPIC = config['gcp']['pubsub']['market_data_topic']
OUTPUT_TOPIC = config['gcp']['pubsub']['enriched_features_topic']

# Import feature computation
from app.features.compute import compute_features


def callback(message):
    """
    Called when a message is received from Pub/Sub.
    """
    try:
        # Parse incoming bar
        bar_data = json.loads(message.data.decode("utf-8"))
        print(f"📥 Received bar: {bar_data['symbol']} @ {bar_data['timestamp']}")

        # Compute features
        features = compute_features(bar_data)

        if features is not None:
            # Publish to enriched-features
            publish_bar(PROJECT_ID, OUTPUT_TOPIC, features)
        else:
            print(f"🟡 Skipped feature computation for {bar_data['symbol']} — insufficient data")

        # Acknowledge message
        message.ack()

    except Exception as e:
        print(f"❌ Error processing message: {e}")
        message.nack()  # Re-deliver


def start_feature_subscriber():
    """
    Start the subscriber to market-data-bars.
    """
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, "market-data-bars-sub")

    print(f"👂 Listening to Pub/Sub: {INPUT_TOPIC} (subscription: {subscription_path})")
    print("💡 Computing features in real-time...\n")

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

    try:
        streaming_pull_future.result(timeout=None)
    except KeyboardInterrupt:
        print("\n🛑 Stopping feature subscriber...")
        streaming_pull_future.cancel()
    except Exception as e:
        print(f"❌ Subscriber error: {e}")
        streaming_pull_future.cancel()
    finally:
        subscriber.close()
