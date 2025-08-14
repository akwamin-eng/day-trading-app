# test_publish.py
from app.utils.publisher import publish_bar

data = {
    "symbol": "AAPL",
    "open": 175.23,
    "high": 175.41,
    "low": 175.18,
    "close": 175.35,
    "volume": 1243,
    "timestamp": "2025-08-13 10:30:00",
    "data_source": "alpaca-test"
}

publish_bar("day-trading-app-468901", "market-data-bars", data)
