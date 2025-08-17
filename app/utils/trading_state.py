# app/utils/trading_state.py

"""
Global trading state flag.
Persists to disk so it survives restarts.
"""

import json
import os

STATE_FILE = "trading_logs/trading_state.json"

def load_state():
    """Load current trading state. Default: enabled."""
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("enabled", True)
    except Exception:
        return True  # Default: trading enabled

def save_state(enabled: bool):
    """Save trading state to disk."""
    os.makedirs("trading_logs", exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"enabled": enabled}, f, indent=2)

# Global flag
TRADING_ENABLED = load_state()
