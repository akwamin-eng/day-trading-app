# main.py
"""
Production entry point for AI trading system.
Starts all services: ingestion, feature engine, sentiment, ML, execution.
"""

import os
import subprocess
import time
import signal
import sys

# List of services to run
SERVICES = [
    "python -c 'from app.data.ingest import start_ingest; start_ingest()'",
    "python -c 'from app.features.subscriber import start_feature_subscriber; start_feature_subscriber()'",
    "python -c 'from app.sentiment.fetcher import start_news_sentiment_pipeline; start_news_sentiment_pipeline()'",
    "python -c 'from app.ml.subscriber import start_ml_merger; start_ml_merger()'",
    "python -c 'from app.execution.executor import start_executor; start_executor()'"
]

processes = []

def signal_handler(signum, frame):
    print("\n🛑 Shutting down all services...")
    for p in processes:
        p.terminate()
    for p in processes:
        p.wait()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    print("🚀 Starting AI Trading System...")

    for cmd in SERVICES:
        print(f"✅ Starting: {cmd}")
        p = subprocess.Popen(cmd, shell=True)
        processes.append(p)
        time.sleep(2)  # Stagger startup

    try:
        # Keep main process alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
