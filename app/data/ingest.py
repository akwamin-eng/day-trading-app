# app/data/ingest.py

"""
Secure Data Ingestion Service
- Loads Alpaca keys from GCP Secret Manager
- Connects to real-time 1-minute bars
- Respects market hours
"""

import asyncio
from datetime import datetime
import yaml

# Alpaca SDK
from alpaca.data.live import StockDataStream

# Local utilities
from app.utils.market_hours import is_market_open
from app.utils.secrets import get_alpaca_keys

# Add this import at the top (near others)
from app.utils.publisher import publish_bar
from app.utils.config import get_config

# Load config once at module level
config = get_config()
GCP_PROJECT_ID = config['gcp']['project_id']
MARKET_DATA_TOPIC = config['gcp']['pubsub']['market_data_topic']

# ----------------------------
# Load Config
# ----------------------------

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

config = load_config()
SYMBOLS = config['alpaca']['symbols']


# ----------------------------
# Get Secure Credentials
# ----------------------------

try:
    alpaca_keys = get_alpaca_keys()
    API_KEY = alpaca_keys['api_key']
    SECRET_KEY = alpaca_keys['secret_key']
except Exception as e:
    print(f"❌ Failed to load Alpaca keys from Secret Manager: {e}")
    print("💡 Make sure secrets 'alpaca-api-key' and 'alpaca-secret-key' exist in GCP.")
    raise


# ----------------------------
# Initialize Data Stream
# ----------------------------

wss_client = StockDataStream(API_KEY, SECRET_KEY)


# ----------------------------
# Updated Bar Event Handler
# ----------------------------

async def on_bar(bar):
    """
    Callback: Called when a new 1-minute bar is received.
    Converts bar to dict and publishes to GCP Pub/Sub.
    """
    # Convert bar to dictionary
    bar_dict = {
        "symbol": bar.symbol,
        "open": round(float(bar.open), 2),
        "high": round(float(bar.high), 2),
        "low": round(float(bar.low), 2),
        "close": round(float(bar.close), 2),
        "volume": int(bar.volume),
        "timestamp": bar.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": "alpaca"
    }

    # Publish to Pub/Sub
    publish_bar(GCP_PROJECT_ID, MARKET_DATA_TOPIC, bar_dict)

    # Optional: Also print to console
    print(f"""
📈 BAR PUBLISHED: {bar_dict['symbol']}
  Time:    {bar_dict['timestamp']}
  Open:    ${bar_dict['open']}
  High:    ${bar_dict['high']}
  Low:     ${bar_dict['low']}
  Close:   ${bar_dict['close']}
  Volume:  {bar_dict['volume']}
  ---""")

# ----------------------------
# Main: Run Ingestion
# ----------------------------

async def main():
    print(f"🚀 Data ingestion starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Connecting to Alpaca for symbols: {SYMBOLS}")
    print("💡 Waiting for 1-minute bars...\n")

    # WebSocket logging
    wss_client._connection._callbacks.on_ws_open = lambda ws: print("🟢 WebSocket OPENED")
    wss_client._connection._callbacks.on_ws_close = lambda ws, code, msg: print(f"🔴 WebSocket CLOSED: {code} | {msg}")
    wss_client._connection._callbacks.on_ws_error = lambda ws, err: print(f"❌ WebSocket ERROR: {err}")

    # Subscribe to bars
    for symbol in SYMBOLS:
        wss_client.subscribe_bars(on_bar, symbol)
        print(f"📌 Subscribed to {symbol}")

    try:
        while is_market_open():
            if not wss_client._running:
                print("⚠️ Stream stopped. Exiting.")
                break
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Manual stop requested.")
    except Exception as e:
        print(f"🚨 Error in ingestion: {e}")
    finally:
        print("🔚 Stopping data stream...")
        await wss_client.stop()
        print("✅ Ingestion stopped gracefully.")


# ----------------------------
# Run (via main.py)
# ----------------------------

if __name__ == "__main__":
    from app.utils.market_hours import is_market_open
    if not is_market_open():
        print("❌ Market is closed. Run via `python main.py` for auto-wakeup.")
    else:
        asyncio.run(main())
