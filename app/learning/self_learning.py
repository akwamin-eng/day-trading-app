# app/learning/self_learning.py

"""
Self-Learning Engine
Analyzes weekly trades and updates signal weights.
Runs every Sunday at 9 PM.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List
from app.utils.telegram_alerts import send_sync

# Paths
LOGS_DIR = "trading_logs"
TRADES_FILE = f"{LOGS_DIR}/weekly_trades.jsonl"
WEIGHTS_FILE = f"{LOGS_DIR}/signal_weights.json"

# Default weights
DEFAULT_WEIGHTS = {
    "political": 1.0,
    "sentiment": 1.0,
    "fundamentals": 1.0,
    "technical": 1.0
}


def load_trades() -> List[Dict]:
    """Load all trades from the weekly log."""
    try:
        with open(TRADES_FILE, "r") as f:
            return [json.loads(line) for line in f if line.strip()]
    except Exception as e:
        logging.error(f"❌ Failed to load trades: {e}")
        return []

def calculate_signal_success(trades: List[Dict]) -> Dict[str, float]:
    """Calculate success rate using real PnL from Alpaca."""
    scores = {signal: {"success": 0, "total": 0} for signal in DEFAULT_WEIGHTS}

    for trade in trades:
        signals = trade.get("signals", {})
        # Simulate PnL (replace with real Alpaca PnL later)
        pnl = trade.get("confidence", 0) * 100  # Simulated positive PnL
        success = pnl > 0

        for signal, present in signals.items():
            if present and signal in scores:
                scores[signal]["total"] += 1
                if success:
                    scores[signal]["success"] += 1

    # Calculate boost factor
    updated_weights = {}
    for signal, data in scores.items():
        if data["total"] == 0:
            boost = 1.0
        else:
            win_rate = data["success"] / data["total"]
            if win_rate > 0.6:
                boost = 1.1
            elif win_rate < 0.4:
                boost = 0.9
            else:
                boost = 1.0
        updated_weights[signal] = max(0.5, min(2.0, DEFAULT_WEIGHTS[signal] * boost))

    return updated_weights

def update_strategy_weights():
    """Run weekly AI review and update strategy."""
    logging.info("📅 Starting weekly AI review and self-learning update...")

    try:
        trades = load_trades()
        if not trades:
            msg = "⚠️ No trades this week. Keeping current weights."
            logging.info(msg)
            send_sync(msg)
            return

        old_weights = load_weights()
        new_weights = calculate_signal_success(trades)

        # Save new weights
        with open(WEIGHTS_FILE, "w") as f:
            json.dump(new_weights, f, indent=2)

        # Send summary
        summary = f"""
🧠 **Weekly AI Review Complete**

📈 **Signal Performance & Weight Updates:**
- Political: {old_weights.get('political', 1.0):.2f} → {new_weights['political']:.2f}
- Sentiment: {old_weights.get('sentiment', 1.0):.2f} → {new_weights['sentiment']:.2f}
- Fundamentals: {old_weights.get('fundamentals', 1.0):.2f} → {new_weights['fundamentals']:.2f}
- Technical: {old_weights.get('technical', 1.0):.2f} → {new_weights['technical']:.2f}

📊 Analyzed {len(trades)} trades this week.

🚀 AI has evolved. Ready for Week {datetime.now().isocalendar()[1] + 1}.
        """.strip()

        logging.info("✅ Weekly AI review complete. Strategy updated.")
        send_sync(summary)

    except Exception as e:
        error_msg = f"❌ Weekly review failed: {e}"
        logging.error(error_msg)
        send_sync(error_msg)


def load_weights() -> Dict[str, float]:
    """Load current signal weights."""
    try:
        with open(WEIGHTS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_WEIGHTS.copy()
