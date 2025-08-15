# app/execution/executor.py

"""
AI Trading Executor
Listens to trading signals and executes paper trades via Alpaca.
Uses dynamic sizing, stop-loss, take-profit, and Telegram alerts.
"""

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest, OrderClass
from alpaca.trading.enums import OrderSide, TimeInForce
from google.cloud import pubsub_v1
from app.utils.secrets import get_paper_api_key, get_paper_secret_key
from app.risk.position import get_position_size
from app.utils.telegram import send_sync
import json
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load credentials
API_KEY = get_paper_api_key()
SECRET_KEY = get_paper_secret_key()
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# Track positions (optional)
_positions = {}


def execute_order(symbol: str, signal: str, price: float):
    """
    Place a bracket order with 2% stop-loss and 4% take-profit.
    Ensures take-profit is at least $0.01 above entry price.
    """
    try:
        # Get dynamic position size
        qty = get_position_size(symbol, API_KEY, SECRET_KEY)
        if qty < 1:
            logging.warning(f"⚠️ Position size < 1 for {symbol}, using 1 share")
            qty = 1

        # Define stop-loss and take-profit prices
        sl_price = round(price * 0.98, 2)  # 2% below entry
        tp_price = round(price * 1.04, 2)  # 4% above entry

        # Ensure take-profit is at least $0.01 above entry price (Alpaca requirement)
        min_tp = round(price + 0.01, 2)
        tp_price = max(tp_price, min_tp)

        # Create bracket order
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if signal == "Buy" else OrderSide.SELL,
            time_in_force=TimeInForce.GTC,  # Good 'til canceled
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=tp_price),
            stop_loss=StopLossRequest(stop_price=sl_price)
        )

        # Submit order
        submitted_order = trading_client.submit_order(order)
        logging.info(
            f"✅ {signal} {qty} shares of {symbol} | "
            f"SL: ${sl_price} | TP: ${tp_price} | Order ID: {submitted_order.id}"
        )

        # Update position tracking
        _positions[symbol] = _positions.get(symbol, 0) + (qty if signal == "Buy" else -qty)

        # Send Telegram alert
        send_sync(
            f"🎯 **Trade Executed**\n"
            f"📊 {signal} {qty} {symbol}\n"
            f"💰 Price: ${price:.2f}\n"
            f"📉 Stop-Loss: ${sl_price}\n"
            f"📈 Take-Profit: ${tp_price}"
        )

    except Exception as e:
        error_msg = f"❌ Failed to execute {signal} order for {symbol}: {e}"
        logging.error(error_msg)

        # Send failure alert
        send_sync(f"🚨 **Trade Failed**\n{error_msg}")


def signal_callback(message):
    """
    Called when a new trading signal is received via Pub/Sub.
    """
    try:
        data = json.loads(message.data.decode("utf-8"))
        symbol = data['symbol']
        signal = data['signal']
        price = data['price']
        confidence = data.get('confidence', 0.5)

        # Risk management: skip low-confidence signals
        if confidence < 0.55:
            logging.info(f"🟡 Skipping {signal} for {symbol} | Confidence: {confidence:.2f}")
            message.ack()
            return

        # Only act on Buy/Sell
        if signal in ["Buy", "Sell"]:
            execute_order(symbol, signal, price)
        elif signal == "Hold":
            logging.info(f"⏸️ Hold signal for {symbol} | No action")
        else:
            logging.warning(f"❓ Unknown signal: {signal}")

        # Acknowledge message
        message.ack()

    except Exception as e:
        logging.error(f"❌ Error processing signal: {e}")
        message.nack()  # Re-queue on error


def start_executor():
    """
    Start listening to trading signals and execute paper trades.
    """
    # Pub/Sub setup
    subscriber = pubsub_v1.SubscriberClient()
    PROJECT_ID = "day-trading-app-468901"
    subscription_path = subscriber.subscription_path(PROJECT_ID, "trading-signals-sub")

    logging.info("💼 Paper Trading Executor Started...")
    logging.info("💡 Listening to trading signals and executing paper trades...\n")

    # Create subscription if it doesn't exist
    try:
        subscriber.create_subscription(
            name=subscription_path,
            topic=f"projects/{PROJECT_ID}/topics/trading-signals"
        )
        logging.info(f"✅ Created subscription: {subscription_path}")
    except Exception as e:
        if "already exists" in str(e):
            logging.info(f"🔁 Subscription already exists: {subscription_path}")
        else:
            logging.error(f"❌ Subscription error: {e}")

    # Start listening
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=signal_callback)

    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        logging.info("\n🛑 Executor stopped.")
        streaming_pull_future.cancel()
    finally:
        subscriber.close()
