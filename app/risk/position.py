# app/risk/position.py

"""
Dynamic position sizing using Alpaca REST API directly.
"""

import logging
import requests
from alpaca.trading.client import TradingClient

def get_position_size(symbol: str, api_key: str, secret_key: str, risk_percent: float = 0.01) -> int:
    """
    Calculate position size based on 1% risk and 2% stop-loss.
    Uses direct REST API call to get latest trade.
    """
    try:
        # Get account equity
        trading_client = TradingClient(api_key, secret_key, paper=True)
        account = trading_client.get_account()
        equity = float(account.equity)

        # Fetch latest trade via Alpaca REST API
        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/trades/latest"
        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key
        }
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            price = resp.json()["trade"]["p"]
        else:
            # Fallback: use last quote if trade not available (e.g., market closed)
            quote_url = f"https://data.alpaca.markets/v2/stocks/{symbol}/quotes/latest"
            q_resp = requests.get(quote_url, headers=headers)
            if q_resp.status_code == 200:
                quote = q_resp.json()["quote"]
                price = (quote["ap"] + quote["bp"]) / 2  # ask + bid / 2
            else:
                logging.warning(f"⚠️ No trade or quote data for {symbol}, using fallback price")
                price = 175.0  # Fallback price (set to a reasonable default)

        # Assume 2% stop-loss
        stop_distance = 0.02
        risk_per_share = price * stop_distance

        # Risk 1% of equity
        risk_amount = equity * risk_percent
        qty = int(risk_amount / risk_per_share)

        return max(1, qty)

    except Exception as e:
        logging.error(f"❌ Failed to calculate position size for {symbol}: {e}")
        return 1  # Default to 1 share
