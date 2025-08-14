# dashboard.py

"""
Live AI Trading Dashboard
Displays real-time signals, portfolio, and performance.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import time
from google.cloud import pubsub_v1
import os

# --- Configuration ---
PROJECT_ID = "day-trading-app-468901"
TRADING_SIGNALS_TOPIC = "trading-signals"
ENRICHED_FEATURES_TOPIC = "enriched-features"
NEWS_SENTIMENT_TOPIC = "news-sentiment"

# Use in-memory storage for demo (in prod, use Firestore or BigQuery)
signals_log = []
features_log = []
sentiment_log = []

st.set_page_config(page_title="AI Trading Dashboard", layout="wide")
st.title("🧠 AI Trading Dashboard")
st.markdown("Live monitoring of signals, portfolio, and performance")

# --- Sidebar ---
st.sidebar.header("Settings")
refresh_interval = st.sidebar.slider("Refresh every (seconds)", 1, 10, 5)
show_news = st.sidebar.checkbox("Show News Sentiment", True)
show_features = st.sidebar.checkbox("Show Technical Features", True)

# --- Initialize Pub/Sub ---
subscriber = pubsub_v1.SubscriberClient()

def create_subscription(topic_name, subscription_name):
    try:
        subscription_path = subscriber.subscription_path(PROJECT_ID, subscription_name)
        topic_path = f"projects/{PROJECT_ID}/topics/{topic_name}"
        subscriber.create_subscription(name=subscription_path, topic=topic_path)
        st.sidebar.success(f"✅ Sub created: {subscription_name}")
    except Exception as e:
        if "already exists" in str(e):
            pass
        else:
            st.sidebar.error(f"❌ Sub error: {e}")

create_subscription(TRADING_SIGNALS_TOPIC, "dashboard-signals-sub")
create_subscription(ENRICHED_FEATURES_TOPIC, "dashboard-features-sub")
create_subscription(NEWS_SENTIMENT_TOPIC, "dashboard-sentiment-sub")

# --- Callbacks ---
def on_signal(message):
    try:
        data = json.loads(message.data.decode("utf-8"))
        data["received_at"] = pd.Timestamp.now()
        signals_log.append(data)
        message.ack()
    except Exception as e:
        message.nack()

def on_feature(message):
    try:
        data = json.loads(message.data.decode("utf-8"))
        data["received_at"] = pd.Timestamp.now()
        features_log.append(data)
        message.ack()
    except Exception as e:
        message.nack()

def on_sentiment(message):
    try:
        data = json.loads(message.data.decode("utf-8"))
        data["received_at"] = pd.Timestamp.now()
        sentiment_log.append(data)
        message.ack()
    except Exception as e:
        message.nack()

# Start listeners
streaming_pull_future1 = subscriber.subscribe(
    subscriber.subscription_path(PROJECT_ID, "dashboard-signals-sub"),
    callback=on_signal
)
streaming_pull_future2 = subscriber.subscribe(
    subscriber.subscription_path(PROJECT_ID, "dashboard-features-sub"),
    callback=on_feature
)
streaming_pull_future3 = subscriber.subscribe(
    subscriber.subscription_path(PROJECT_ID, "dashboard-sentiment-sub"),
    callback=on_sentiment
)

# --- Auto-refresh ---
placeholder = st.empty()

# --- Main Loop ---
while True:
    with placeholder.container():
        col1, col2 = st.columns(2)

        # --- Trading Signals ---
        with col1:
            st.subheader("🎯 Live Trading Signals")
            if signals_log:
                df_signals = pd.DataFrame(signals_log[-20:])  # Last 20
                st.dataframe(df_signals[["symbol", "signal", "confidence", "price", "timestamp"]])
                
                # Signal counts
                st.bar_chart(df_signals["signal"].value_counts())
            else:
                st.write("📡 Waiting for signals...")

        # --- Portfolio Value (Simulated) ---
        with col2:
            st.subheader("💰 Portfolio Value")
            if signals_log:
                df = pd.DataFrame(signals_log)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                df['pnl'] = (df['price'] - df['price'].iloc[0]) * 10  # $10 per trade
                df['cum_pnl'] = df['pnl'].cumsum()

                fig, ax = plt.subplots()
                ax.plot(df['timestamp'], df['cum_pnl'], marker="o")
                ax.set_title("Cumulative PnL")
                ax.set_ylabel("PnL ($)")
                plt.xticks(rotation=45)
                st.pyplot(fig)
            else:
                st.write("📊 No trades yet.")

        # --- News Sentiment ---
        if show_news:
            st.subheader("📰 Latest News Sentiment")
            if sentiment_log:
                df_sentiment = pd.DataFrame(sentiment_log[-10:])
                st.dataframe(df_sentiment[["symbol", "headline", "sentiment", "confidence", "publishedAt"]])
            else:
                st.write("📡 Waiting for news...")

        # --- Technical Features ---
        if show_features:
            st.subheader("📊 Technical Features")
            if features_log:
                df_features = pd.DataFrame(features_log[-5:])
                st.dataframe(df_features[["symbol", "timestamp", "price", "rsi", "bb_percent_b", "volume_ratio"]])
            else:
                st.write("📡 Waiting for features...")

        st.divider()
        st.caption(f"Updated: {pd.Timestamp.now()} | Refresh: {refresh_interval}s")

    time.sleep(refresh_interval)
