# app/learning/self_learning.py

"""
Auto-adjust signal weights based on PnL
"""

import json
import logging
from datetime import datetime

LOG_FILE = "trading_logs/weekly_trades.jsonl"
WEIGHTS_FILE = "trading_logs/signal_weights.json"

def load_trades():
    with open(LOG_FILE) as f:
        return [json.loads(line) for line in f if line.strip()]

def update_weights():
    trades = load_trades()
    scores = {"political": [], "sentiment": [], "technical": [], "fundamentals": []}

    for trade in trades:
        signals = trade["signals"]
        # Simulate PnL (replace with real Alpaca PnL later)
        pnl = trade["confidence"] * 100  # Simulated
        for sig, active in signals.items():
            if active:
                scores[sig].append(1 if pnl > 0 else 0)

    new_weights = {}
    for sig, results in scores.items():
        win_rate = sum(results) / len(results) if results else 0.5
        if win_rate > 0.6:
            new_weights[sig] = 1.1
        elif win_rate < 0.4:
            new_weights[sig] = 0.9
        else:
            new_weights[sig] = 1.0

    with open(WEIGHTS_FILE, "w") as f:
        json.dump(new_weights, f, indent=2)

    logging.info(f"🧠 Updated weights: {new_weights}")
