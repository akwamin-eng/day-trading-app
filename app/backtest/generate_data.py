# app/backtest/generate_data.py

"""
Generate synthetic historical data for backtesting.
Simulates price, volume, and news sentiment.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

def generate_synthetic_data(days=30, symbols=['AAPL', 'TSLA']):
    np.random.seed(42)
    n = days * 390  # 390 minutes per trading day

    # Use 'min' instead of deprecated 'T'
    dates = pd.date_range('2025-07-01', periods=n, freq='min')
    
    # Filter to trading hours: 9:30 AM – 4:00 PM, Mon–Fri
    trading_dates = []
    for dt in dates:
        if (dt.time() >= datetime.strptime('09:30', '%H:%M').time() and 
            dt.time() <= datetime.strptime('16:00', '%H:%M').time() and 
            dt.dayofweek < 5):
            trading_dates.append(dt)
    
    # Take only the first `n` valid trading minutes
    trading_dates = trading_dates[:n]

    data = []
    for symbol in symbols:
        base_price = np.random.choice([150, 250, 800], p=[0.5, 0.3, 0.2])
        price = base_price
        for dt in trading_dates:
            # Simulate trend + noise + news shocks
            drift = 0.0002  # Small positive drift
            volatility = 0.02  # Base volatility
            noise = np.random.normal(0, volatility)  # Now noise is always valid
            shock = np.random.choice([0, 0.05, -0.05], p=[0.95, 0.03, 0.02])  # News event
            log_return = drift + noise + shock
            price *= (1 + log_return)
            volume = np.random.randint(500, 5000)

            # Add sentiment shock
            sentiment_score = 0.0
            if abs(shock) > 0:
                sentiment_score = shock / 0.05  # +1 or -1

            data.append({
                'symbol': symbol,
                'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'open': round(price * (1 + np.random.uniform(-0.005, 0.005)), 2),
                'high': round(price * (1 + np.random.uniform(0, 0.01)), 2),
                'low': round(price * (1 - np.random.uniform(0, 0.01)), 2),
                'close': round(price, 2),
                'volume': volume,
                'sentiment_score': round(sentiment_score, 2)
            })

    df = pd.DataFrame(data)
    df.to_csv('app/backtest/historical_data.csv', index=False)
    print(f"✅ Generated {len(df)} rows of synthetic data for {days} days")

if __name__ == "__main__":
    generate_synthetic_data()
