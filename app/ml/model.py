# app/ml/model.py

"""
Train and save a Random Forest model for trading signal prediction.
Uses synthetic data with technical + sentiment features.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os


def generate_synthetic_data(n_days=30, symbols=['AAPL', 'TSLA', 'MSFT']):
    """
    Generate realistic synthetic market data with:
    - Price trends and volatility
    - Technical indicators
    - Sentiment shocks
    """
    np.random.seed(42)
    n = n_days * 390  # 390 minutes per trading day
    base_price_levels = {'AAPL': 175, 'TSLA': 250, 'MSFT': 400}

    # Time index: trading hours only (9:30–16:00), Mon–Fri
    dates = pd.date_range('2025-07-01', periods=n, freq='min')
    trading_dates = [
        dt for dt in dates
        if (dt.time() >= pd.Timestamp('09:30').time() and
            dt.time() <= pd.Timestamp('16:00').time() and
            dt.dayofweek < 5)
    ][:n]

    data = []
    for symbol in symbols:
        price = base_price_levels[symbol]
        for dt in trading_dates:
            # Simulate mean-reverting trend with drift
            drift = 0.0001
            volatility = 0.02
            noise = np.random.normal(0, volatility)
            
            # News sentiment shock (rare but impactful)
            sentiment_shock = 0.0
            if np.random.random() < 0.03:  # 3% chance per minute
                sentiment_shock = np.random.choice([0.08, -0.08], p=[0.5, 0.5])

            log_return = drift + noise + sentiment_shock
            price *= (1 + log_return)
            volume = np.random.randint(800, 5000)

            # Add correlated technical features
            sma_short = price * (1 + np.random.uniform(-0.01, 0.01))
            sma_medium = price * (1 + np.random.uniform(-0.02, 0.02))
            sma_long = price * (1 + np.random.uniform(-0.03, 0.03))
            rsi = 50 + (price % 50)  # Simulate oscillation
            bb_percent_b = 0.5 + (np.sin(price / 10) + 1) / 2  # Oscillate 0–1
            momentum = price - sma_short
            atr = volatility * price
            volume_ratio = volume / 2000

            # Target: will price go up next minute?
            future_price = price * (1 + np.random.normal(0.0001, 0.02) + sentiment_shock)
            target = 1 if future_price > price else 0

            data.append({
                'symbol': symbol,
                'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'price': round(price, 2),
                'sma_short': round(sma_short, 2),
                'sma_medium': round(sma_medium, 2),
                'sma_long': round(sma_long, 2),
                'rsi': round(rsi, 2),
                'bb_percent_b': round(bb_percent_b, 2),
                'momentum': round(momentum, 2),
                'atr': round(atr, 2),
                'volume_ratio': round(volume_ratio, 2),
                'sentiment_score': sentiment_shock * 10,  # Scale for model
                'target': target
            })

    df = pd.DataFrame(data)
    print(f"✅ Generated {len(df)} synthetic data points for {n_days} days")
    return df


def train_model():
    """Train Random Forest model and save to disk."""
    print("🧠 Training ML model...")

    # Generate data
    df = generate_synthetic_data()

    # Feature columns (must match production)
    feature_cols = [
        'sma_short', 'sma_medium', 'sma_long',
        'rsi', 'bb_percent_b', 'momentum',
        'atr', 'volume_ratio', 'sentiment_score'
    ]

    X = df[feature_cols]
    y = df['target']

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"✅ Model trained. Test Accuracy: {accuracy:.3f}")
    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Down', 'Up']))

    # Save model
    model_dir = 'app/ml'
    os.makedirs(model_dir, exist_ok=True)
    model_path = f'{model_dir}/model.pkl'
    joblib.dump(model, model_path)
    print(f"💾 Model saved to {model_path}")

    # Optional: Feature importance
    importances = model.feature_importances_
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': importances
    }).sort_values('importance', ascending=False)
    print("\n🔍 Feature Importance:")
    print(feature_importance.to_string(index=False))

    return model


if __name__ == "__main__":
    train_model()
