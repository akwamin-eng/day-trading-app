# app/learning/self_learning.py

"""
Self-Learning Engine
Analyzes past trades and adjusts signal weights to improve future performance.
Runs weekly after the AI review.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

# Paths to logs and weights
LOGS_DIR = "trading_logs"
WEIGHTS_FILE = os.path.join(LOGS_DIR, "signal_weights.json")

# Default signal weights (0.0 to 1.0)
DEFAULT_WEIGHTS = {
    "political": 1.0,        # House/Senate trades
    "sentiment": 1.0,        # GNews / FinBERT sentiment
    "fundamentals": 1.0,     # Alpha Vantage company health
    "technical": 1.0         # RSI, Bollinger, trend
}


def load_weights() -> Dict[str, float]:
    """Load current signal weights from file, or return defaults."""
    if not os.path.exists(WEIGHTS_FILE):
        logging.info("⚙️ No existing weights found. Using defaults.")
        return DEFAULT_WEIGHTS.copy()

    try:
        with open(WEIGHTS_FILE, "r") as f:
            weights = json.load(f)
            logging.info(f"✅ Loaded weights: {weights}")
            return weights
    except Exception as e:
        logging.error(f"❌ Failed to load weights: {e}. Using defaults.")
        return DEFAULT_WEIGHTS.copy()


def save_weights(weights: Dict[str, float]):
    """Save updated weights to file."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    try:
        with open(WEIGHTS_FILE, "w") as f:
            json.dump(weights, f, indent=2)
        logging.info(f"💾 Saved updated weights: {weights}")
    except Exception as e:
        logging.error(f"❌ Failed to save weights: {e}")


def analyze_trade_performance(trades: List[Dict]) -> Optional[Dict[str, float]]:
    """
    Analyze trade outcomes and return adjustment factors for each signal.
    Increases weight if signal predicted winners, decreases if linked to losers.
    """
    adjustments = {k: 1.0 for k in DEFAULT_WEIGHTS.keys()}

    total_profitable = 0
    signal_success = {k: 0 for k in adjustments}
    signal_count = {k: 0 for k in adjustments}

    for trade in trades:
        try:
            outcome = trade.get("pnl", 0) > 0  # True if profitable
            signals = trade.get("signals", {})

            if outcome:
                total_profitable += 1

            for signal in signal_count:
                if signals.get(signal, False):
                    signal_count[signal] += 1
                    if outcome:
                        signal_success[signal] += 1

        except Exception as e:
            logging.warning(f"⚠️ Failed to analyze trade: {e}")
            continue

    # Update adjustment factors
    for signal in adjustments:
        count = signal_count[signal]
        success = signal_success[signal]
        success_rate = success / count if count > 0 else 0.0

        if success_rate > 0.6:
            adjustments[signal] = 1.1  # Boost weight by 10%
        elif success_rate < 0.4:
            adjustments[signal] = 0.9  # Reduce weight by 10%
        else:
            adjustments[signal] = 1.0  # No change

        logging.info(f"📊 {signal}: {success}/{count} wins ({success_rate:.2f}) → adjustment: x{adjustments[signal]}")

    return adjustments


def update_strategy_weights():
    """
    Main function: Load trade logs, analyze performance, update weights.
    """
    log_file = os.path.join(LOGS_DIR, "weekly_trades.jsonl")
    if not os.path.exists(log_file):
        logging.warning(f"⚠️ No trade log found at {log_file}. Skipping self-learning.")
        return

    trades = []
    with open(log_file, "r") as f:
        for line in f:
            try:
                trades.append(json.loads(line.strip()))
            except Exception as e:
                logging.warning(f"⚠️ Failed to parse log line: {e}")

    if not trades:
        logging.info("ℹ️ No trades to learn from this week.")
        return

    logging.info(f"🧠 Starting self-learning from {len(trades)} trades")

    # Load current weights
    weights = load_weights()

    # Analyze performance
    adjustments = analyze_trade_performance(trades)
    if not adjustments:
        return

    # Apply adjustments
    updated_weights = {sig: weights[sig] * adjustments[sig] for sig in weights}
    logging.info(f"📈 Updated weights before normalization: {updated_weights}")

    # Normalize to prevent runaway scaling
    max_weight = max(updated_weights.values())
    normalized_weights = {k: v / max_weight for k, v in updated_weights.items()}
    logging.info(f"🎯 Final normalized weights: {normalized_weights}")

    # Save
    save_weights(normalized_weights)

    # Send summary (optional: hook into Telegram later)
    print(f"✅ Self-learning complete. Updated strategy weights based on {len(trades)} trades.")


# === Main Execution (for testing) ===
if __name__ == "__main__":
    print("🧪 Running self-learning engine...")
    update_strategy_weights()
