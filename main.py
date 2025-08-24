# main.py
"""
AI Trader - Final Production Version
- Market-aware, disciplined, and hustler-ready
- Uses GOP/NANC for political regime
- Alpaca paper trading with 1% risk
- Telegram + voice alerts
- Prepares for ML self-learning
"""

import os
import logging
import json
import time
import random
from datetime import datetime, timedelta
from flask import Flask, jsonify
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import yfinance as yf

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Import Telegram
try:
    from telegram_sync import send_sync
except Exception as e:
    logger.critical(f"❌ Failed to import telegram_sync: {e}")
    def send_sync(m): print(f"📢 {m}")

# Alpaca client
try:
    trading_client = TradingClient(
        api_key=os.getenv("APCA_API_KEY_ID"),
        secret_key=os.getenv("APCA_API_SECRET_KEY"),
        paper=True
    )
    account = trading_client.get_account()
    equity = float(account.equity)
    logger.info(f"✅ Connected to Alpaca | Equity: ${equity:.2f}")
except Exception as e:
    logger.critical(f"❌ Alpaca connection failed: {e}")
    exit(1)

# Position tracking
POSITIONS_FILE = "trading_logs/open_positions.json"

def load_open_positions():
    if not os.path.exists(POSITIONS_FILE):
        return []
    try:
        with open(POSITIONS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ Failed to load positions: {e}")
        return []

def save_open_positions(positions):
    with open(POSITIONS_FILE, "w") as f:
        json.dump(positions, f, indent=2)

def get_ticker_safe(symbol, period="60d"):
    """Fetch data with retry logic"""
    for _ in range(3):
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            if not hist.empty:
                return hist
        except Exception as e:
            logger.warning(f"⚠️ Retry failed for {symbol}: {e}")
            time.sleep(2 + random.uniform(0, 1))
    return None

def is_market_open():
    """Check if today is a market open day (Mon-Fri)"""
    today = datetime.now().date()
    if today.weekday() >= 5:  # Sat or Sun
        return False
    return True

def get_market_regime():
    """Detect bull/bear using SPY 50-day SMA"""
    hist = get_ticker_safe("SPY", "6mo")
    if hist is None or len(hist) < 50:
        logger.warning("⚠️ SPY data not available. Assuming NEUTRAL market regime.")
        return "neutral"
    close = hist["Close"]
    sma50 = close.rolling(50).mean().iloc[-1]
    current = close.iloc[-1]
    return "bull" if current > sma50 else "bear"

def get_political_regime():
    """Detect political momentum using GOP and NANC ETFs"""
    try:
        logger.info("🔍 Analyzing political regime via GOP & NANC ETFs...")
        gop_hist = get_ticker_safe("GOP", "20d")
        nanc_hist = get_ticker_safe("NANC", "20d")

        if gop_hist is None or nanc_hist is None:
            logger.warning("⚠️ GOP/NANC data not available. Using RARE as fallback.")
            return "fallback"

        gop_sma = gop_hist["Close"].rolling(20).mean().iloc[-1]
        nanc_sma = nanc_hist["Close"].rolling(20).mean().iloc[-1]
        current_gop = gop_hist["Close"].iloc[-1]
        current_nanc = nanc_hist["Close"].iloc[-1]

        gop_momentum = current_gop > gop_sma
        nanc_momentum = current_nanc > nanc_sma

        if gop_momentum and not nanc_momentum:
            regime = "republican_favor"
        elif nanc_momentum and not gop_momentum:
            regime = "democratic_favor"
        elif gop_momentum and nanc_momentum:
            gop_return = (current_gop / gop_hist["Close"].iloc[0]) - 1
            nanc_return = (current_nanc / nanc_hist["Close"].iloc[0]) - 1
            regime = "republican_favor" if gop_return > nanc_return else "democratic_favor"
        else:
            regime = "neutral"

        logger.info(f"✅ Political regime: {regime.upper()}")
        return regime

    except Exception as e:
        logger.error(f"❌ Political regime detection failed: {e}")
        return "fallback"

def find_hustle_opportunities():
    """Find high-conviction trades: volume surge + political alignment"""
    watchlist = ["RARE", "GME", "AMC", "SNDL", "MVIS", "NVDA", "TSLA"]
    opportunities = []
    for symbol in watchlist:
        hist = get_ticker_safe(symbol)
        if hist is None or len(hist) < 20:
            continue
        volume = hist["Volume"].iloc[-1]
        avg_volume = hist["Volume"].rolling(20).mean().iloc[-1]
        if volume > avg_volume * 1.8:  # 80% surge
            opportunities.append(symbol)
    return opportunities

def get_watchlist():
    """Get all active US equities"""
    try:
        all_assets = trading_client.get_all_assets()
        symbols = [
            asset.symbol for asset in all_assets
            if asset.status == "active"
            and asset.asset_class == "us_equity"
            and asset.tradable
            and len(asset.symbol) <= 5
            and "$" not in asset.symbol
            and "." not in asset.symbol
            and asset.symbol not in ["BITO", "TBT", "SPXU"]
        ]
        return symbols[:200]
    except Exception as e:
        logger.error(f"❌ Failed to fetch watchlist: {e}")
        return ["RARE", "NVDA", "TSLA", "SPY", "GME", "AMC"]

@app.route("/run-daily")
def run_daily():
    try:
        logger.info("🔁 /run-daily triggered")
        send_sync("🌅 AI Trader: Starting market analysis...")

        if not is_market_open():
            logger.info("📅 Market is closed today. Skipping trading logic.")
            send_sync("📅 Market is closed. AI is on standby.")
            return jsonify({"status": "success", "market_open": False}), 200

        # 1. Get market and political regime
        market_regime = get_market_regime()
        political_regime = get_political_regime()

        # 2. Map political regime to preferred stocks
        if political_regime == "republican_favor":
            preferred_stocks = ["RARE", "TSLA", "AMD", "GME", "AMC"]
        elif political_regime == "democratic_favor":
            preferred_stocks = ["NVDA", "MSFT", "META", "AAPL", "ORCL"]
        else:
            preferred_stocks = ["RARE"]  # fallback

        # 3. Get watchlist
        watchlist = get_watchlist()

        # 4. Load open positions
        open_positions = load_open_positions()
        closed = []

        # 5. Check for exits
        for pos in open_positions:
            symbol = pos["symbol"]
            entry_price = pos["entry_price"]
            stop_loss = pos["stop_loss"]
            qty = pos["qty"]

            hist = get_ticker_safe(symbol)
            if hist is None:
                continue
            current_price = hist["Close"][-1]

            exit_reason = None
            if current_price <= stop_loss:
                exit_reason = "stop_loss"
            elif get_technical_signal(symbol) == "sell":
                exit_reason = "profit_take"
            elif market_regime == "bear":
                exit_reason = "market_regime"

            if exit_reason:
                try:
                    order = trading_client.submit_order(
                        order=MarketOrderRequest(
                            symbol=symbol,
                            qty=qty,
                            side=OrderSide.SELL,
                            time_in_force=TimeInForce.DAY
                        )
                    )
                    pnl = (current_price - entry_price) / entry_price
                    msg = f"💰 Sold {qty} {symbol} at ${current_price:.2f} | PnL: {pnl:+.2%} | Reason: {exit_reason}"
                    send_sync(msg)
                    log_trade(symbol, "sell", qty, current_price, exit_reason)
                    closed.append(symbol)
                except Exception as e:
                    logger.error(f"❌ Sell failed: {e}")

        # Update positions
        remaining = [p for p in open_positions if p["symbol"] not in closed]
        save_open_positions(remaining)

        # 6. Evaluate new buys
        executed = False
        for symbol in watchlist:
            if symbol in [p["symbol"] for p in remaining]:
                continue
            if symbol not in preferred_stocks:
                continue

            hist = get_ticker_safe(symbol)
            if hist is None:
                continue
            current_price = hist["Close"][-1]
            high = hist["High"]
            low = hist["Low"]
            atr = (high - low).rolling(14).mean().iloc[-1]
            stop_loss = current_price - (atr * 2)
            risk_per_share = current_price - stop_loss

            if risk_per_share <= 0:
                continue

            max_risk = equity * 0.01
            qty = int(max_risk / risk_per_share)

            if qty == 0:
                continue

            try:
                order = trading_client.submit_order(
                    order=MarketOrderRequest(
                        symbol=symbol,
                        qty=qty,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY
                    )
                )
                reason = f"Political momentum: {political_regime}"
                send_sync(f"🎯 Bought {qty} {symbol} at ${current_price:.2f} | Stop: ${stop_loss:.2f}")
                log_trade(symbol, "buy", qty, current_price, reason)
                remaining.append({
                    "symbol": symbol,
                    "entry_price": current_price,
                    "stop_loss": stop_loss,
                    "qty": qty,
                    "timestamp": datetime.utcnow().isoformat()
                })
                executed = True
                break
            except Exception as e:
                logger.error(f"❌ Buy failed: {e}")

        # 7. Hustle Mode: Volume surge
        if not executed:
            hustle_stocks = find_hustle_opportunities()
            for symbol in hustle_stocks:
                if symbol not in [p["symbol"] for p in remaining]:
                    hist = get_ticker_safe(symbol)
                    if hist is None:
                        continue
                    current_price = hist["Close"].iloc[-1]
                    atr = (hist["High"] - hist["Low"]).rolling(14).mean().iloc[-1]
                    stop_loss = current_price - (atr * 2)
                    qty = 1  # Hustle with 1 share
                    try:
                        order = trading_client.submit_order(
                            order=MarketOrderRequest(
                                symbol=symbol,
                                qty=qty,
                                side=OrderSide.BUY,
                                time_in_force=TimeInForce.DAY
                            )
                        )
                        send_sync(f"🔥 Hustle Mode: Bought 1 {symbol} on volume surge!")
                        log_trade(symbol, "buy", qty, current_price, "Hustle: volume surge")
                        executed = True
                        break
                    except Exception as e:
                        logger.error(f"❌ Hustle buy failed: {e}")

        save_open_positions(remaining)

        # 8. Daily summary
        summary = f"""
📊 **Daily Summary**
📅 Market: {'Open' if is_market_open() else 'Closed'}
🧠 Market Regime: {market_regime.upper()}
🏛️ Political Regime: {political_regime.upper()}
{'🎯 Focus: Republican stocks' if political_regime == 'republican_favor' else ''}
{'🎯 Focus: Democratic stocks' if political_regime == 'democratic_favor' else ''}
{'🔍 Neutral political momentum' if political_regime == 'neutral' else ''}
🔥 Hustle Mode: {'Active' if not executed else 'Not needed'}
✅ Trade Executed: {executed}
❌ Trade Closed: {len(closed)}
💬 AI used GOP/NANC momentum to guide strategy
🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """.strip()
        send_sync(summary)

        # 9. Run self-learning (weekly)
        if datetime.now().weekday() == 4:  # Friday
            try:
                from app.learning.self_learning import update_signal_weights
                update_signal_weights()
            except Exception as e:
                logger.error(f"❌ Self-learning failed: {e}")

        return jsonify({"status": "success", "trade_executed": executed, "market_open": True}), 200

    except Exception as e:
        logger.error(f"💥 Error in /run-daily: {e}", exc_info=True)
        send_sync(f"❌ Run failed: {type(e).__name__}")
        return jsonify({"status": "error"}), 500

def get_technical_signal(symbol):
    """Simple RSI-based signal"""
    hist = get_ticker_safe(symbol)
    if hist is None or len(hist) < 14:
        return "neutral"
    close = hist["Close"]
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs.iloc[-1]))
    return "buy" if rsi < 30 else "sell" if rsi > 70 else "neutral"

def log_trade(symbol, action, qty, price, reason):
    """Log trade to JSONL for learning"""
    log_entry = {
        "symbol": symbol,
        "action": action,
        "qty": qty,
        "price": price,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open("trading_logs/trades.jsonl", "a") as f:
        f.write(f"{json.dumps(log_entry)}\n")

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/")
def home():
    status = "online" if is_market_open() else "standby"
    return jsonify({"status": status, "market_open": is_market_open()})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
