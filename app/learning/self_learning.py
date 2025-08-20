# app/learning/self_learning.py

"""
Self-Learning Engine
Analyzes paper trades and updates signal weights based on PnL
"""

import json
import logging
import os
from datetime import datetime, timedelta

# Setup
logging.basicConfig(level=logging.INFO)
LOG_FILE = "trading_logs/weekly_trades.jsonl"
WEIGHTS_FILE = "trading_logs/signal_weights.json"
DEFAULT_WEIGHTS = {
    "political": 1.0,
    "sentiment": 1.0,
    "fundamentals": 1.0,
    "technical": 1.0
}


def load_trades(days=1):
    """Load trades from last N days"""
    if not os.path.exists(LOG_FILE):
        logging.info("📊 No trade logs found")
        return []

    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    trades = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            try:
                trade = json.loads(line.strip())
                if trade["timestamp"] >= cutoff:
                    trades.append(trade)
            except Exception as e:
                logging.warning(f"⚠️ Failed to parse trade: {e}")
    logging.info(f"📊 Loaded {len(trades)} trades from last {days} day(s)")
    return trades


def calculate_win_rate(trades, signal_name):
    """Calculate win rate for a given signal"""
    if not trades:
        return 0.5  # Neutral

    results = []
    for trade in trades:
        # Simulated PnL: use confidence * 100 for now
        pnl = trade.get("confidence", 0.5) * 100
        if trade.get("signals", {}).get(signal_name, False):
            results.append(1 if pnl > 0 else 0)

    return sum(results) / len(results) if results else 0.5


def update_signal_weights():
    """Update weights based on recent performance"""
    logging.info("🧠 Starting self-learning engine...")

    trades = load_trades(days=1)
    if not trades:
        logging.info("🧠 No trades today — keeping current weights")
        return

    try:
        with open(WEIGHTS_FILE, "r") as f:
            current_weights = json.load(f)
    except Exception as e:
        logging.warning(f"⚠️ Could not load weights: {e}. Using defaults.")
        current_weights = DEFAULT_WEIGHTS.copy()

    new_weights = {}
    for signal in current_weights.keys():
        win_rate = calculate_win_rate(trades, signal)
        if win_rate > 0.6:
            new_weights[signal] = current_weights[signal] * 1.1  # Boost
        elif win_rate < 0.4:
            new_weights[signal] = current_weights[signal] * 0.9  # Reduce
        else:
            new_weights[signal] = current_weights[signal]  # Keep

    # Save updated weights
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(new_weights, f, indent=2)

    logging.info(f"✅ Updated signal weights: {new_weights}")


if __name__ == "__main__":
    update_signal_weights()
