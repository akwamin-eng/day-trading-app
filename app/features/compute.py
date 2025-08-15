# app/features/compute.py

"""
Feature Engineering Module
Computes technical indicators using pandas-ta (pure Python).
Replaces ta-lib to ensure compatibility with Cloud Run.
"""

import pandas as pd
import pandas_ta as ta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def compute_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute technical analysis features from OHLCV data.
    
    Args:
        df (pd.DataFrame): DataFrame with columns: timestamp, open, high, low, close, volume
    
    Returns:
        pd.DataFrame: DataFrame with original data + technical features
    """
    if df.empty:
        logging.warning("⚠️ Empty DataFrame in compute_technical_features")
        return df

    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)

    # Ensure numeric columns
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows with missing price data
    df.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)
    if df.empty:
        logging.warning("⚠️ No valid OHLC data after cleaning")
        return df

    # === Momentum Indicators ===
    # RSI (Relative Strength Index)
    df['rsi'] = ta.rsi(df['close'], length=14)

    # MACD (Moving Average Convergence Divergence)
    macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
    if macd is not None:
        df = pd.concat([df, macd], axis=1)

    # Stochastic RSI
    stoch_rsi = ta.stochrsi(df['close'], length=14, rsi_length=14, k=3, d=3)
    if stoch_rsi is not None:
        df = pd.concat([df, stoch_rsi[['STOCHRSIk_14_14_3_3', 'STOCHRSId_14_14_3_3']]], axis=1)
        df.rename(columns={
            'STOCHRSIk_14_14_3_3': 'stoch_rsi_k',
            'STOCHRSId_14_14_3_3': 'stoch_rsi_d'
        }, inplace=True)

    # === Volatility Indicators ===
    # Bollinger Bands
    bbands = ta.bbands(df['close'], length=20, std=2)
    if bbands is not None:
        df = pd.concat([df, bbands], axis=1)
        df.rename(columns={
            'BBU_20_2.0': 'bb_upper',
            'BBM_20_2.0': 'bb_middle',
            'BBL_20_2.0': 'bb_lower'
        }, inplace=True)
        # Band width and %B
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_percent'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

    # ATR (Average True Range)
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)

    # === Trend Indicators ===
    # Simple Moving Averages
    df['sma_20'] = ta.sma(df['close'], length=20)
    df['sma_50'] = ta.sma(df['close'], length=50)
    df['sma_200'] = ta.sma(df['close'], length=200)

    # EMA (Exponential Moving Average)
    df['ema_12'] = ta.ema(df['close'], length=12)
    df['ema_26'] = ta.ema(df['close'], length=26)

    # Golden/Death Cross Signal
    df['golden_cross'] = (df['sma_20'] > df['sma_50']) & (df['sma_20'].shift(1) <= df['sma_50'].shift(1))
    df['death_cross'] = (df['sma_20'] < df['sma_50']) & (df['sma_20'].shift(1) >= df['sma_50'].shift(1))

    # === Volume Indicators ===
    # Volume SMA
    df['volume_sma_20'] = ta.sma(df['volume'], length=20)
    df['volume_ratio'] = df['volume'] / df['volume_sma_20']

    # OBV (On-Balance Volume)
    df['obv'] = ta.obv(df['close'], df['volume'])

    # === Candlestick Patterns (Optional) ===
    # Doji
    df['candle_range'] = df['high'] - df['low']
    df['candle_body'] = abs(df['close'] - df['open'])
    df['is_doji'] = df['candle_body'] / df['candle_range'] < 0.1  # Body < 10% of range

    # === Feature Cleanup ===
    # Forward-fill to handle any remaining NaNs
    df.fillna(method='ffill', inplace=True)
    df.fillna(method='bfill', inplace=True)

    logging.info(f"✅ Computed technical features for {len(df)} records")
    return df


# === Test Function (Optional) ===
if __name__ == "__main__":
    # Create mock OHLCV data
    dates = pd.date_range("2025-08-01", periods=100, freq="1min")
    price = 170.0
    prices = [price]
    for _ in range(99):
        price += (0.5 - 0.1) * 0.1 + (0.5 - 0.1) * 0.05
        prices.append(price)

    test_df = pd.DataFrame({
        'timestamp': dates,
        'open': [p * 0.995 for p in prices],
        'high': [p * 1.01 for p in prices],
        'low': [p * 0.985 for p in prices],
        'close': prices,
        'volume': [1000 + i * 10 for i in range(100)]
    })

    # Compute features
    result_df = compute_technical_features(test_df)
    print(result_df[['timestamp', 'close', 'rsi', 'bb_upper', 'bb_lower', 'macd_12_26_9']].tail())
