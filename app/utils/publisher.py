# app/utils/publisher.py

"""
Secure Pub/Sub publisher for market data.
"""

import json
from google.cloud import pubsub_v1
from google.api_core.exceptions import GoogleAPICallError, RetryError

# Global publisher client (created once)
_publisher_client = None


def get_publisher_client():
    """
    Lazily initialize and return the Pub/Sub publisher client.
    """
    global _publisher_client
    if _publisher_client is None:
        _publisher_client = pubsub_v1.PublisherClient()
    return _publisher_client


def publish_bar(project_id, topic_id, bar_data):
    """
    Publish a bar message to Pub/Sub.

    Args:
        project_id (str): GCP project ID
        topic_id (str): Pub/Sub topic ID (e.g., 'market-data-bars')
        bar_data (dict): Bar data to publish

    Returns:
        str: Message ID if successful, None otherwise
    """
    client = get_publisher_client()
    topic_path = client.topic_path(project_id, topic_id)

    try:
        # Convert dict to JSON bytes
        data = json.dumps(bar_data).encode("utf-8")

        # Publish message
        future = client.publish(topic_path, data)
        message_id = future.result(timeout=10)  # Blocks until published

        print(f"📤 Published bar to {topic_id}: {bar_data['symbol']} @ {bar_data['timestamp']} | MsgID: {message_id}")
        return message_id

    except (GoogleAPICallError, RetryError) as e:
        print(f"❌ Google API Error publishing to {topic_id}: {e}")
    except Exception as e:
        print(f"❌ Unexpected error publishing message: {e}")

    return None
