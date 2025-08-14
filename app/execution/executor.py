# app/execution/executor.py

"""
AI Trading Executor
Listens to trading signals and executes paper trades via Alpaca.
"""

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from google.cloud import pubsub_v1
from app.utils.secrets import get_paper_api_key, get_paper_secret_key
from app.utils.config import get_config
import json
import time

# Load config
config = get_config()
PROJECT_ID = config['gcp']['project_id']
SIGNALS_TOPIC = config['gcp']['pubsub']['trading_signals_topic']

# Alpaca Paper Trading Client
API_KEY = get_paper_api_key()
SECRET_KEY = get_paper_secret_key()
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# Track positions
_positions = {}


def execute_order(symbol: str, side: str, qty: int):
    """
    Place a market order.
    """
    try:
        market_order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side == "Buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        order = trading_client.submit_order(market_order)
        print(f"✅ {side} {qty} shares of {symbol} | Order ID: {order.id}")
    except Exception as e:
        print(f"❌ Failed to execute {side} order for {symbol}: {e}")


def signal_callback(message):
    """
    Called when a new trading signal is received.
    """
    try:
        data = json.loads(message.data.decode("utf-8"))
        symbol = data['symbol']
        signal = data['signal']
        price = data['price']
        confidence = data['confidence']

        # Risk management
        if confidence < 0.55:
            print(f"🟡 Skipping {signal} for {symbol} | Low confidence: {confidence:.2f}")
            message.ack()
            return

        qty = 10  # Fixed position size (adjust as needed)

        if signal == "Buy":
            if _positions.get(symbol, 0) <= 0:
                execute_order(symbol, "Buy", qty)
                _positions[symbol] = _positions.get(symbol, 0) + qty
        elif signal == "Sell":
            if _positions.get(symbol, 0) >= 0:
                execute_order(symbol, "Sell", qty)
                _positions[symbol] = _positions.get(symbol, 0) - qty
        elif signal == "Hold":
            pass

        print(f"📊 Portfolio: {_positions}")

        # Acknowledge message
        message.ack()

    except Exception as e:
        print(f"❌ Error processing signal: {e}")
        message.nack()


def start_executor():
    """
    Start listening to trading signals and execute paper trades.
    """
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, "trading-signals-sub")

    print("💼 Paper Trading Executor Started...")
    print("💡 Listening to trading signals and executing paper trades...\n")

    # Create subscription if not exists
    try:
        subscriber.create_subscription(name=subscription_path, topic=f"projects/{PROJECT_ID}/topics/{SIGNALS_TOPIC}")
        print(f"✅ Created subscription: {subscription_path}")
    except Exception as e:
        if "already exists" in str(e):
            print(f"🔁 Subscription already exists: {subscription_path}")
        else:
            print(f"❌ Subscription error: {e}")

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=signal_callback)

    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        print("\n🛑 Executor stopped.")
        streaming_pull_future.cancel()
    finally:
        subscriber.close()
