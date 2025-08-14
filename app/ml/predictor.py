# app/ml/predictor.py

"""
Load trained model and predict trading signals.
"""

import joblib
import numpy as np
from app.utils.publisher import publish_bar
from app.utils.config import get_config

# Load config
config = get_config()
PROJECT_ID = config['gcp']['project_id']
SIGNALS_TOPIC = config['gcp']['pubsub']['trading_signals_topic']

# Load model
_model = joblib.load('app/ml/model.pkl')
_feature_order = [
    'sma_short', 'sma_medium', 'rsi', 'bb_percent_b',
    'momentum', 'atr', 'volume_ratio', 'sentiment_score'
]

def predict_signal(merged_features: dict):
    """
    Predict Buy/Sell/Hold signal from merged features.
    """
    # Extract features in correct order
    X = np.array([[
        merged_features[col] for col in _feature_order
    ]])

    # Predict
    proba = _model.predict_proba(X)[0]
    pred = _model.predict(X)[0]
    confidence = max(proba)

    # Map to signal
    signal = "Buy" if pred == 1 else "Sell"
    if confidence < 0.55:
        signal = "Hold"

    # Publish
    message = {
        "symbol": merged_features['symbol'],
        "timestamp": merged_features['timestamp'],
        "signal": signal,
        "confidence": round(confidence, 4),
        "price": merged_features['price'],
        "proba_buy": round(proba[1], 4),
        "proba_sell": round(proba[0], 4),
        "source": "ml-predictor"
    }

    publish_bar(PROJECT_ID, SIGNALS_TOPIC, message)
    print(f"🎯 SIGNAL: {signal} | Conf: {confidence:.2f} | Price: ${merged_features['price']}")
