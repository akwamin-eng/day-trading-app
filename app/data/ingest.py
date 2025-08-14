# app/data/ingest.py

"""
Data Ingestion Service
Connects to Alpaca's real-time WebSocket stream and ingests 1-minute bars
for configured stocks during U.S. market hours.
"""

import asyncio
from datetime import datetime
import yaml

# Alpaca SDK
from alpaca.data.live import StockDataStream

# Local utilities
from app.utils.market_hours import is_market_open


# ----------------------------
# Configuration Loading
# ----------------------------

def load_config():
    """Load configuration from YAML file."""
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)


# Load config at module level
config = load_config()

# Extract Alpaca settings
API_KEY = config['alpaca']['api_key']
SECRET_KEY = config['alpaca']['secret_key']
SYMBOLS = config['alpaca']['symbols']


# ----------------------------
# Initialize Data Stream
# ----------------------------

wss_client = StockDataStream(API_KEY, SECRET_KEY)


# ----------------------------
# Bar Event Handler
# ----------------------------

async def on_bar(bar):
    """
    Callback function triggered when a new 1-minute bar is received.
    """
    print(f"""
📈 NEW BAR: {bar.symbol}
  Time:    {bar.timestamp.strftime('%Y-%m-%d %H:%M')}
  Open:    ${bar.open:.2f}
  High:    ${bar.high:.2f}
  Low:     ${bar.low:.2f}
  Close:   ${bar.close:.2f}
  Volume:  {bar.volume}
  ---""")


# ----------------------------
# Main: Run Ingestion
# ----------------------------

async def main():
    """
    Main entry point for the ingestion service.
    Starts the stream during market hours and shuts down gracefully.
    """
    print(f"🚀 Data ingestion starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Connecting to Alpaca for symbols: {SYMBOLS}")
    print("💡 Waiting for 1-minute bars...\n")

    # Set up WebSocket connection logging
    def on_open(ws):
        print("🟢 WebSocket connection OPENED")

    def on_close(ws, close_code, close_msg):
        print(f"🔴 WebSocket CLOSED: {close_code} | {close_msg}")

    def on_error(ws, error):
        print(f"❌ WebSocket ERROR: {error}")

    wss_client._connection._callbacks.on_ws_open = on_open
    wss_client._connection._callbacks.on_ws_close = on_close
    wss_client._connection._callbacks.on_ws_error = on_error

    # Subscribe to 1-minute bars for each symbol
    for symbol in SYMBOLS:
        wss_client.subscribe_bars(on_bar, symbol)
        print(f"📌 Subscribed to 1-minute bars: {symbol}")

    try:
        # Keep running only while market is open
        print("⏳ Running... Awaiting first bar.")
        while is_market_open():
            if not wss_client._running:
                print("⚠️ Stream stopped unexpectedly. Exiting.")
                break
            await asyncio.sleep(1)  # Small sleep to prevent busy loop
    except KeyboardInterrupt:
        print("\n🛑 Manual interrupt received. Shutting down...")
    except Exception as e:
        print(f"🚨 Unexpected error in ingestion loop: {e}")
    finally:
        print("🔚 Stopping data stream...")
        await wss_client.stop()
        print("✅ Ingestion service stopped gracefully.")


# ----------------------------
# Run as Standalone (Optional)
# ----------------------------

# This allows running: `python app/data/ingest.py`
# But preferred: use `main.py`
if __name__ == "__main__":
    import sys
    from app.utils.market_hours import is_market_open

    if not is_market_open():
        print("❌ Market is closed. This service only runs during market hours.")
        print("💡 Run `python main.py` instead — it handles scheduling automatically.")
        sys.exit(0)

    asyncio.run(main())
