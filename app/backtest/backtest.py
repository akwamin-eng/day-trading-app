# app/backtest/backtest.py

"""
Backtest the ML prediction engine on historical data.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import json

# Load data
df = pd.read_csv('app/backtest/historical_data.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Sort by symbol and time
df = df.sort_values(['symbol', 'timestamp'])

# Compute features (same as in production)
WINDOW_SHORT = 10
WINDOW_MEDIUM = 20
WINDOW_LONG = 50

def compute_features(group):
    g = group.copy()
    g['sma_short'] = g['close'].rolling(WINDOW_SHORT).mean()
    g['sma_medium'] = g['close'].rolling(WINDOW_MEDIUM).mean()
    g['sma_long'] = g['close'].rolling(WINDOW_LONG).mean()
    g['rsi'] = 100 - (100 / (1 + (g['close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / 
                                 abs(g['close'].diff()).rolling(14).mean())))
    g['bb_upper'] = g['close'].rolling(20).mean() + 2 * g['close'].rolling(20).std()
    g['bb_lower'] = g['close'].rolling(20).mean() - 2 * g['close'].rolling(20).std()
    g['bb_percent_b'] = (g['close'] - g['bb_lower']) / (g['bb_upper'] - g['bb_lower'])
    g['momentum'] = g['close'] - g['close'].shift(WINDOW_SHORT)
    g['atr'] = (g['high'] - g['low']).rolling(14).mean()
    g['volume_ratio'] = g['volume'] / g['volume'].rolling(20).mean()
    return g

df = df.groupby('symbol').apply(compute_features).reset_index(drop=True)

# Forward-fill sentiment
df['sentiment_score'] = df['sentiment_score'].fillna(method='ffill').fillna(0)

# Prepare features
feature_cols = ['sma_short', 'sma_medium', 'sma_long', 'rsi', 'bb_percent_b',
                'momentum', 'atr', 'volume_ratio', 'sentiment_score']
df = df.dropna(subset=feature_cols)

# Load model
model = joblib.load('app/ml/model.pkl')

# Predict
X = df[feature_cols]
probs = model.predict_proba(X)
preds = model.predict(X)

# True future movement
df['future_close'] = df.groupby('symbol')['close'].shift(-1)
df['target'] = (df['future_close'] > df['close']).astype(int)
y_true = df['target'].dropna().values

# Align predictions
y_pred = preds[-len(y_true):]

# Metrics
print("📊 MODEL EVALUATION")
print(f"Accuracy:  {accuracy_score(y_true, y_pred):.3f}")
print(f"Precision: {precision_score(y_true, y_pred):.3f}")
print(f"Recall:    {recall_score(y_true, y_pred):.3f}")
print(f"F1 Score:  {f1_score(y_true, y_pred):.3f}")

# Simulate trading
df_valid = df.iloc[-len(y_true):].copy()
df_valid['signal'] = preds[-len(y_true):]
df_valid['position'] = df_valid['signal']  # 1 = long, 0 = flat
df_valid['returns'] = df_valid.groupby('symbol')['close'].pct_change() * df_valid['position'].shift()
sharpe = df_valid['returns'].mean() / df_valid['returns'].std() * np.sqrt(252*390)  # Annualized

print(f"Sharpe Ratio: {sharpe:.3f}")
print(f"Total Return: {df_valid['returns'].sum():.3f}")
