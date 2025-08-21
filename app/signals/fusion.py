# app/signals/fusion.py

"""
Signal Fusion Engine
- Buy & Sell with full PnL tracking
- 1% Risk Rule, ATR sizing, top-down filter
- AI voice alerts via Telegram
- Rate-limited FMP calls to avoid 429 errors
"""

import json
import requests
import logging
import time
import random
from typing import Dict, Optional
from datetime import datetime
import os

# Delayed import (set in main.py)
send_sync = None

# === CONFIGURATION ===
FMP_API_KEY = "ZqXPebgZUwpofOO3MUxNlCY4Iu9Mkw1c"
FMP_TECHNICAL_URL = "https://financialmodelingprep.com/api/v3/technical_indicator/daily/{symbol}"
FMP_HISTORICAL_URL = "https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
FMP_PROFILE_URL = "https://financialmodelingprep.com/api/v3/profile/{symbol}"
FMP_QUOTE_URL = "https://financialmodelingprep.com/api/v3/quote/{symbol}"

# Paths
WEIGHTS_FILE = "trading_logs/signal_weights.json"
DEFAULT_WEIGHTS = {
    "political": 1.0,
    "sentiment": 1.0,
    "fundamentals": 1.0,
    "technical": 1.0
}


def load_weights() -> Dict[str, float]:
    """Load learned signal weights."""
    try:
        with open(WEIGHTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"⚠️ Could not load weights: {e}. Using defaults.")
        return DEFAULT_WEIGHTS.copy()


def rate_limited_request(url, params, retries=3):
    """Make a request with rate limiting and exponential backoff."""
    for i in range(retries):
        try:
            time.sleep(0.5 + random.uniform(0, 0.5))  # 0.5–1.0s delay
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 429:
                wait = 2 ** i * 5  # Exponential backoff: 5, 10, 20s
                logging.warning(f"⚠️ Rate limit hit. Waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if i == retries - 1:
                logging.error(f"❌ Failed after {retries} attempts: {e}")
                return None
            time.sleep(1)
    return None


def get_atr(symbol: str, period: int = 14) -> float:
    """Fetch ATR from FMP."""
    url = FMP_TECHNICAL_URL.format(symbol=symbol)
    params = {"type": "atr", "period": period, "apikey": FMP_API_KEY}
    try:
        data = rate_limited_request(url, params)
        return float(data[0]["atr"]) if data else 1.0
    except Exception as e:
        logging.error(f"❌ Failed to fetch ATR for {symbol}: {e}")
        return 1.0


def get_technical_signal(symbol: str) -> str:
    """Fetch RSI from FMP."""
    url = FMP_TECHNICAL_URL.format(symbol=symbol)
    params = {"type": "rsi", "apikey": FMP_API_KEY}
    try:
        data = rate_limited_request(url, params)
        if not data:
            return "neutral"
        rsi = data[0].get("rsi")
        if rsi and rsi < 30:
            return "buy"
        elif rsi and rsi > 70:
            return "sell"
        return "neutral"
    except Exception as e:
        logging.error(f"❌ FMP technical fetch failed for {symbol}: {e}")
        return "neutral"


def get_fundamentals(symbol: str) -> Optional[Dict]:
    """Fetch fundamentals from FMP."""
    url = FMP_PROFILE_URL.format(symbol=symbol)
    params = {"apikey": FMP_API_KEY}
    try:
        data = rate_limited_request(url, params)
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
        return None
    except Exception as e:
        logging.error(f"❌ Failed to fetch fundamentals: {e}")
        return None


def get_market_regime() -> str:
    """Detect bull/bear/neutral using SPY data."""
    url = FMP_HISTORICAL_URL.format(symbol="SPY")
    params = {"apikey": FMP_API_KEY}
    try:
        data = rate_limited_request(url, params)
        if "historical" not in data or len(data["historical"]) < 50:
            return "neutral"
        prices = [day["close"] for day in data["historical"][-50:]]
        sma = sum(prices) / 50
        return "bull" if prices[-1] > sma else "bear"
    except Exception as e:
        logging.error(f"❌ Failed to detect regime: {e}")
        return "neutral"


def is_top_down_aligned(symbol: str) -> bool:
    """Check market, sector, and stock momentum."""
    try:
        market_regime = get_market_regime()
        if market_regime == "bear":
            return False

        sector_map = {
            "RARE": "Technology", "NVDA": "Technology", "AMD": "Technology",
            "TSLA": "Automotive", "AAPL": "Technology", "MSFT": "Technology",
            "GOOGL": "Technology", "META": "Technology"
        }
        sector_momentum = sector_map.get(symbol) == "Technology"

        fundamentals = get_fundamentals(symbol)
        price = float(fundamentals.get("price", 0)) if fundamentals else 0
        sma50 = float(fundamentals.get("sma50", 0)) if fundamentals else 0
        stock_momentum = price > sma50

        aligned = market_regime != "bear" and sector_momentum and stock_momentum
        logging.info(
            f"📊 Top-down check for {symbol}: "
            f"Market={market_regime}, Sector={sector_momentum}, Stock={stock_momentum} → {aligned}"
        )
        return aligned

    except Exception as e:
        logging.error(f"❌ Top-down check failed for {symbol}: {e}")
        return False


def generate_fused_signal(symbol: str, political_buy: bool = False):
    """Generate buy signal."""
    logging.info(f"🔍 Evaluating {symbol} | Political Buy: {political_buy}")
    weights = load_weights()
    total_score = 0.0
    reasons = []

    if political_buy:
        total_score += 1.0 * weights["political"]
        reasons.append("Rep bought")
    else:
        logging.info(f"❌ No political buy for {symbol}")

    sentiment_score = 0.7
    if sentiment_score > 0.5:
        total_score += 1.0 * weights["sentiment"]
        reasons.append(f"Sentiment: {sentiment_score:.2f}")
    else:
        logging.info(f"❌ Negative sentiment for {symbol}")

    fundamentals = get_fundamentals(symbol)
    peg_ratio = float(fundamentals.get("priceToEarningsRatio", 999)) if fundamentals else 999
    if fundamentals and peg_ratio < 1.0:
        total_score += 1.0 * weights["fundamentals"]
        reasons.append(f"PEG: {peg_ratio:.2f}")
    else:
        logging.info(f"❌ Weak fundamentals for {symbol}")

    tech_signal = get_technical_signal(symbol)
    if tech_signal == "buy":
        total_score += 1.0 * weights["technical"]
        reasons.append("RSI < 30")
    elif tech_signal == "sell":
        logging.info(f"❌ Technical sell signal for {symbol}")
        return None
    else:
        logging.info(f"❌ Neutral technical signal for {symbol}")

    regime = get_market_regime()
    if regime == "bear":
        total_score *= 0.5
        logging.info(f"📉 Market regime: {regime.upper()} → reducing signal strength")
    else:
        logging.info(f"📈 Market regime: {regime.upper()} → normal confidence")

    if not is_top_down_aligned(symbol):
        logging.info(f"❌ {symbol} failed top-down filter")
        return None

    if total_score >= 2.5:
        atr = get_atr(symbol)
        if atr <= 0:
            logging.warning(f"⚠️ ATR is invalid for {symbol} → skipping trade")
            return None

        entry_price = float(fundamentals.get("price", 0)) if fundamentals else 0
        if entry_price <= 0:
            logging.warning(f"⚠️ Invalid entry price for {symbol} → skipping trade")
            return None

        stop_loss_price = entry_price - (atr * 2)
        risk_per_share = entry_price - stop_loss_price

        if risk_per_share <= 0:
            logging.warning(f"⚠️ Invalid risk_per_share for {symbol} → skipping trade")
            return None

        account_capital = 100000
        max_risk_per_trade = account_capital * 0.01
        qty = int(max_risk_per_trade / risk_per_share)

        if qty == 0:
            logging.info(f"❌ Position size 0 for {symbol} (risk too high)")
            return None

        confidence = min(total_score / 4.0, 1.0)
        logging.info(
            f"✅ High-conviction signal for {symbol} "
            f"(Score: {total_score:.2f}, Confidence: {confidence:.2f}, Qty: {qty})"
        )

        return {
            "symbol": symbol,
            "action": "buy",
            "confidence": confidence,
            "quantity": qty,
            "entry_price": entry_price,
            "stop_loss": stop_loss_price,
            "reason": ", ".join(reasons),
            "regime": regime
        }
    else:
        logging.info(f"❌ Total score {total_score:.2f} < 2.5 → no signal for {symbol}")
        return None


def generate_exit_signal(symbol: str, entry_price: float, stop_loss: float, qty: int):
    """Generate sell signal."""
    try:
        url = FMP_QUOTE_URL.format(symbol=symbol)
        params = {"apikey": FMP_API_KEY}
        data = rate_limited_request(url, params)
        current_price = data[0]["price"] if data else 0.0

        if current_price <= 0:
            return None

        if current_price <= stop_loss:
            logging.info(f"📉 {symbol} hit stop-loss (${stop_loss:.2f}) → SELL")
            return {
                "action": "sell",
                "reason": "stop_loss",
                "exit_price": current_price,
                "pnl": (current_price - entry_price) / entry_price,
                "qty": qty
            }

        tech_signal = get_technical_signal(symbol)
        if tech_signal == "sell":
            logging.info(f"🎯 {symbol} RSI > 70 → SELL for profit")
            return {
                "action": "sell",
                "reason": "profit_take",
                "exit_price": current_price,
                "pnl": (current_price - entry_price) / entry_price,
                "qty": qty
            }

        regime = get_market_regime()
        if regime == "bear":
            logging.info(f"📉 Market turned bearish → SELL {symbol}")
            return {
                "action": "sell",
                "reason": "market_regime",
                "exit_price": current_price,
                "pnl": (current_price - entry_price) / entry_price,
                "qty": qty
            }

        return None

    except Exception as e:
        logging.error(f"❌ Failed to generate exit signal for {symbol}: {e}")
        return None


def execute_paper_trade(signal: Dict):
    """Execute paper buy."""
    try:
        qty = signal.get("quantity", 1)
        if qty == 0:
            logging.info("❌ Position size is 0 — skipping trade")
            return

        logging.info(f"✅ Paper trade executed: Buy {qty} shares of {signal['symbol']} at ${signal['entry_price']:.2f}")
        logging.info(f"📉 Stop Loss: ${signal['stop_loss']:.2f}")

        message = f"""
🎯 **High-Conviction Buy Signal**
📊 {signal['symbol']} (Confidence: {signal['confidence']:.2f})
💡 {signal['reason']}
🧮 Qty: {qty}
💰 Entry: ${signal['entry_price']:.2f}
🛑 Stop Loss: ${signal['stop_loss']:.2f}
🌍 Market: {signal['regime'].upper()}
📝 Paper trade executed
🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """.strip()
        print(f"📢 Telegram Alert: {message}")
        send_sync(message)

        try:
            from app.utils.voice_alert import send_voice_alert
            voice_text = (
                f"High conviction buy signal. "
                f"Buying {qty} shares of {signal['symbol']} "
                f"at {signal['entry_price']} dollars. "
                f"Stop loss at {signal['stop_loss']} dollars. "
                f"Confidence level: {int(signal['confidence'] * 100)} percent."
            )
            send_voice_alert(
                message=voice_text,
                bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
                chat_id=os.getenv("TELEGRAM_CHAT_ID")
            )
        except Exception as e:
            logging.warning(f"⚠️ Voice alert failed: {e}")

        os.makedirs("trading_logs", exist_ok=True)
        log_entry = {
            "symbol": signal["symbol"],
            "action": "buy",
            "quantity": qty,
            "entry_price": signal["entry_price"],
            "stop_loss": signal["stop_loss"],
            "confidence": signal["confidence"],
            "reason": signal["reason"],
            "regime": signal["regime"],
            "timestamp": datetime.utcnow().isoformat()
        }
        with open("trading_logs/weekly_trades.jsonl", "a") as f:
            f.write(f"{json.dumps(log_entry)}\n")

        positions = load_open_positions()
        positions.append({
            "symbol": signal["symbol"],
            "entry_price": signal["entry_price"],
            "stop_loss": signal["stop_loss"],
            "qty": qty,
            "timestamp": datetime.utcnow().isoformat()
        })
        save_open_positions(positions)

    except Exception as e:
        logging.error(f"❌ Trade execution failed: {e}")


def execute_paper_sell(exit_signal: Dict):
    """Execute paper sell."""
    try:
        symbol = exit_signal["symbol"]
        qty = exit_signal["qty"]
        exit_price = exit_signal["exit_price"]
        pnl = exit_signal["pnl"]

        logging.info(f"✅ Sold {qty} shares of {symbol} at ${exit_price:.2f} | PnL: {pnl:+.2%}")

        message = f"""
💰 **Sell Signal Executed**
📉 {symbol}
🧮 Qty: {qty}
💵 Exit: ${exit_price:.2f}
📊 PnL: {pnl:+.2%}
🛑 Reason: {exit_signal['reason'].replace('_', ' ').title()}
🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """.strip()
        print(f"📢 Telegram Alert: {message}")
        send_sync(message)

        try:
            from app.utils.voice_alert import send_voice_alert
            voice_text = (
                f"Sold {qty} shares of {symbol} at {exit_price} dollars. "
                f"Profit or loss: {pnl:+.1%}. Reason: {exit_signal['reason'].replace('_', ' ')}."
            )
            send_voice_alert(
                message=voice_text,
                bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
                chat_id=os.getenv("TELEGRAM_CHAT_ID")
            )
        except Exception as e:
            logging.warning(f"⚠️ Voice alert failed: {e}")

        log_entry = {
            "symbol": symbol,
            "action": "sell",
            "quantity": qty,
            "exit_price": exit_price,
            "pnl": pnl,
            "reason": exit_signal["reason"],
            "timestamp": datetime.utcnow().isoformat()
        }
        with open("trading_logs/weekly_trades.jsonl", "a") as f:
            f.write(f"{json.dumps(log_entry)}\n")

    except Exception as e:
        logging.error(f"❌ Sell execution failed: {e}")


# === POSITION TRACKING ===

POSITIONS_FILE = "trading_logs/open_positions.json"


def load_open_positions():
    """Load open positions."""
    if not os.path.exists(POSITIONS_FILE):
        return []
    try:
        with open(POSITIONS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"❌ Failed to load open positions: {e}")
        return []


def save_open_positions(positions):
    """Save open positions."""
    with open(POSITIONS_FILE, "w") as f:
        json.dump(positions, f, indent=2)
