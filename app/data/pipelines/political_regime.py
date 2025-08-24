# app/data/pipelines/political_regime.py
"""
Detect political market regime using GOP and NANC ETFs
- GOP: Republican trade momentum
- NANC: Democratic trade momentum
"""
import yfinance as yf
import logging
import os
import json
from datetime import datetime

# Setup
logging.basicConfig(level=logging.INFO)
OUTPUT_FILE = "data/outputs/political_regime.json"

def get_political_regime():
    """Detect if GOP or NANC ETF is in momentum"""
    try:
        logging.info("🔍 Analyzing political regime via GOP & NANC ETFs...")

        # Fetch data
        gop_hist = yf.Ticker("GOP").history(period="20d")
        nanc_hist = yf.Ticker("NANC").history(period="20d")

        if gop_hist.empty or nanc_hist.empty:
            logging.warning("⚠️ Insufficient data for GOP or NANC")
            return "neutral"

        # Calculate 20-day SMA
        gop_sma = gop_hist["Close"].rolling(20).mean().iloc[-1]
        nanc_sma = nanc_hist["Close"].rolling(20).mean().iloc[-1]
        current_gop = gop_hist["Close"].iloc[-1]
        current_nanc = nanc_hist["Close"].iloc[-1]

        # Momentum logic
        gop_momentum = current_gop > gop_sma
        nanc_momentum = current_nanc > nanc_sma

        # Determine regime
        if gop_momentum and not nanc_momentum:
            regime = "republican_favor"
        elif nanc_momentum and not gop_momentum:
            regime = "democratic_favor"
        elif gop_momentum and nanc_momentum:
            # Both up — pick stronger
            gop_return = (current_gop / gop_hist["Close"].iloc[0]) - 1
            nanc_return = (current_nanc / nanc_hist["Close"].iloc[0]) - 1
            regime = "republican_favor" if gop_return > nanc_return else "democratic_favor"
        else:
            regime = "neutral"

        logging.info(f"✅ Political regime: {regime.upper()}")

        # Save for logging
        result = {
            "regime": regime,
            "gop_current": current_gop,
            "gop_sma": gop_sma,
            "nanc_current": nanc_current,
            "nanc_sma": nanc_sma,
            "timestamp": datetime.utcnow().isoformat()
        }
        os.makedirs("data/outputs", exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)

        return regime

    except Exception as e:
        logging.error(f"❌ Political regime detection failed: {e}")
        return "neutral"
