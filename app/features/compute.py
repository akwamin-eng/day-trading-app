# app/features/compute.py

"""
Real-time feature computation for trading.
Calculates technical indicators from price/volume data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

# Rolling window sizes
WINDOW_SHORT = 10    # 10-minute SMA
WINDOW_MEDIUM = 20   # 20-minute SMA, Bollinger Bands
WINDOW_LONG = 50     # 50-minute trend

# State: Keep rolling windows of recent bars per symbol
_bar_cache = {}


def compute_features(bar: Dict) -> Optional[Dict]:
    """
    Compute technical features from a single incoming bar.

    Args:
        bar (dict): Raw bar from Alpaca (symbol, close, volume, etc.)

    Returns:
        dict or None: Enriched feature vector, or None if not enough data
    """
    symbol = bar['symbol']

    # Initialize cache for this symbol
    if symbol not in _bar_cache:
        _bar_cache[symbol] = []

    # Append new bar
    _bar_cache[symbol].append({
        'timestamp': bar['timestamp'],
        'open': bar['open'],
        'high': bar['high'],
        'low': bar['low'],
        'close': bar['close'],
        'volume': bar['volume']
    })

    # Keep only last 60 bars (or more if needed)
    _bar_cache[symbol] = _bar_cache[symbol][-60:]

    # Convert to DataFrame
    df = pd.DataFrame(_bar_cache[symbol])

    # Ensure we have enough data
    if len(df) < WINDOW_MEDIUM:
        return None

    # ----------------------------
    # Compute Features
    # ----------------------------

    features = {
        "symbol": symbol,
        "timestamp": bar['timestamp'],
        "price": bar['close'],
        "volume": bar['volume']
    }

    # 1. Simple Moving Averages
    df['sma_short'] = df['close'].rolling(WINDOW_SHORT).mean()
    df['sma_medium'] = df['close'].rolling(WINDOW_MEDIUM).mean()
    df['sma_long'] = df['close'].rolling(WINDOW_LONG).mean()

    features['sma_short'] = round(df['sma_short'].iloc[-1], 2)
    features['sma_medium'] = round(df['sma_medium'].iloc[-1], 2)
    features['sma_long'] = round(df['sma_long'].iloc[-1], 2)

    # 2. Relative Strength Index (RSI)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(WINDOW_MEDIUM).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(WINDOW_MEDIUM).mean()
    rs = gain / loss.replace(0, 1e-10)  # Avoid division by zero
    rsi = 100 - (100 / (1 + rs))
    features['rsi'] = round(rsi.iloc[-1], 2)

    # 3. Bollinger Bands (%B)
    df['bb_mid'] = df['close'].rolling(WINDOW_MEDIUM).mean()
    bb_std = df['close'].rolling(WINDOW_MEDIUM).std()
    df['bb_upper'] = df['bb_mid'] + 2 * bb_std
    df['bb_lower'] = df['bb_mid'] - 2 * bb_std

    price = bar['close']
    bb_mid = df['bb_mid'].iloc[-1]
    bb_upper = df['bb_upper'].iloc[-1]
    bb_lower = df['bb_lower'].iloc[-1]

    features['bb_percent_b'] = round((price - bb_lower) / (bb_upper - bb_lower), 2) if bb_upper != bb_lower else 0.5

    # 4. Momentum
    momentum = bar['close'] - df['close'].iloc[-WINDOW_SHORT]
    features['momentum'] = round(momentum, 2)

    # 5. Average True Range (ATR) - Simplified
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    avg_true_range = true_range.rolling(WINDOW_SHORT).mean().iloc[-1]
    features['atr'] = round(avg_true_range, 2)

    # 6. Volume SMA and Ratio
    volume_sma = df['volume'].rolling(WINDOW_MEDIUM).mean().iloc[-1]
    features['volume_sma'] = int(volume_sma)
    features['volume_ratio'] = round(bar['volume'] / volume_sma, 2) if volume_sma > 0 else 1.0

    return features
