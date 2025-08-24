# app/learning/self_learning.py
"""
Reinforcement Learning Engine
Updates signal weights based on real PnL from Alpaca paper trades
"""
import json
import logging
import os
from collections import defaultdict

WEIGHTS_FILE = "trading_logs/signal_weights.json"
DEFAULT = {"political": 1.0, "news": 1.0, "technical": 1.0}

def load_trades(days=7):
    if not os.path.exists("trading_logs/trades.jsonl"):
        return []
    trades = []
    with open("trading_logs/trades.jsonl", "r") as f:
        for line in f:
            try:
                trade = json.loads(line.strip())
                trades.append(trade)
            except: pass
    return trades

def update_signal_weights():
    logger = logging.getLogger(__name__)
    logger.info("🧠 Starting Reinforcement Learning...")

    trades = load_trades()
    if not trades:
        logger.info("🧠 No trades yet — keeping current weights")
        return

    # Calculate performance by signal
    results = defaultdict(list)
    for trade in trades:
        if trade["action"] == "sell":
            # Link to buy
            buys = [t for t in trades if t["action"] == "buy" and t["symbol"] == trade["symbol"]]
            if buys:
                buy = buys[-1]
                pnl = trade["pnl"] if "pnl" in trade else 0.0
                if "Political" in buy["reason"]:
                    results["political"].append(pnl)
                if "news" in buy["reason"]:
                    results["news"].append(pnl)
                if "RSI" in buy["reason"]:
                    results["technical"].append(pnl)

    # Update weights
    try:
        with open(WEIGHTS_FILE, "r") as f:
            weights = json.load(f)
    except: weights = DEFAULT.copy()

    new_weights = {}
    for signal, pnl_list in results.items():
        avg_pnl = sum(pnl_list) / len(pnl_list)
        if avg_pnl > 0.015:
            new_weights[signal] = weights.get(signal, 1.0) * 1.1
        elif avg_pnl < -0.005:
            new_weights[signal] = weights.get(signal, 1.0) * 0.9
        else:
            new_weights[signal] = weights.get(signal, 1.0)

    with open(WEIGHTS_FILE, "w") as f:
        json.dump(new_weights, f, indent=2)

    logger.info(f"✅ ML Updated Weights: {new_weights}")
