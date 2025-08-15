# app/risk/position.py

"""
Dynamic Position Sizing
Calculates position size based on 1% account risk and 2% stop-loss.
Uses direct Alpaca REST API calls to avoid SDK version conflicts.
"""

import logging
import requests
from app.utils.secrets import get_paper_api_key, get_paper_secret_key

# Set up logging
logging.basicConfig(level=logging.INFO)

# Risk parameters
RISK_PERCENT = 0.01  # 1% of equity
STOP_DISTANCE = 0.02  # 2% stop-loss

# Cache for prices (simple in-memory cache)
_price_cache = {}
from datetime import datetime, timedelta


def _get_cached_price(symbol: str) -> float:
    """Get cached price if less than 30 seconds old."""
    now = datetime.now()
    if symbol in _price_cache:
        price, timestamp = _price_cache[symbol]
        if now - timestamp < timedelta(seconds=30):
            return price
    return None


def get_position_size(symbol: str, risk_percent: float = RISK_PERCENT) -> int:
    """
    Calculate position size based on 1% risk and 2% stop-loss.
    
    Args:
        symbol (str): Stock symbol
        risk_percent (float): Percent of equity to risk (default 1%)
    
    Returns:
        int: Number of shares to buy
    """
    try:
        # Use cached price if available
        cached_price = _get_cached_price(symbol)
        if cached_price:
            price = cached_price
        else:
            # Get latest price from Alpaca API
            price = _get_latest_price(symbol)
            if not price:
                logging.warning(f"⚠️ Could not get price for {symbol}, using fallback")
                price = 175.0  # Fallback price

            # Cache the price
            _price_cache[symbol] = (price, datetime.now())

        # Get account equity
        equity = _get_account_equity()
        if not equity or equity <= 0:
            logging.error("❌ Invalid account equity")
            return 1

        # Calculate risk per share and position size
        risk_per_share = price * STOP_DISTANCE
        risk_amount = equity * risk_percent
        qty = int(risk_amount / risk_per_share)

        return max(1, qty)

    except Exception as e:
        logging.error(f"❌ Failed to calculate position size for {symbol}: {e}")
        return 1  # Default to 1 share on error


def _get_latest_price(symbol: str) -> float:
    """Get latest trade price from Alpaca Market Data API."""
    api_key = get_paper_api_key()
    secret_key = get_paper_secret_key()
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/trades/latest"

    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()["trade"]["p"]
        else:
            logging.warning(f"⚠️ Trade API failed ({resp.status_code}), trying quote")
            return _get_latest_quote(symbol)
    except Exception as e:
        logging.warning(f"⚠️ Trade API error: {e}, trying quote")
        return _get_latest_quote(symbol)


def _get_latest_quote(symbol: str) -> float:
    """Fallback to bid/ask quote if trade not available."""
    api_key = get_paper_api_key()
    secret_key = get_paper_secret_key()
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/quotes/latest"

    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            quote = resp.json()["quote"]
            return (quote["ap"] + quote["bp"]) / 2  # Midpoint
        else:
            logging.warning(f"⚠️ Quote API failed ({resp.status_code})")
            return None
    except Exception as e:
        logging.warning(f"⚠️ Quote API error: {e}")
        return None


def _get_account_equity() -> float:
    """Get current paper trading account equity."""
    api_key = get_paper_api_key()
    secret_key = get_paper_secret_key()
    url = "https://paper-api.alpaca.markets/v2/account"

    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return float(resp.json()["equity"])
        else:
            logging.error(f"❌ Account API failed: {resp.status_code} {resp.text}")
            return None
    except Exception as e:
        logging.error(f"❌ Account API error: {e}")
        return None
