# app/signals/fusion.py
"""
Fusion Engine: Combine signals into trade decisions
"""
import yfinance as yf
import logging

def get_technical_signal(symbol):
    """Simple RSI from yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="60d")
        if len(hist) < 14:
            return None
        close = hist['Close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs.iloc[-1]))
        return "buy" if rsi < 30 else "sell" if rsi > 70 else "neutral"
    except Exception as e:
        logging.error(f"❌ RSI failed for {symbol}: {e}")
        return "neutral"

def generate_signal(symbol, political_buys, insider_news):
    """Fuse all signals"""
    score = 0
    reasons = []

    if symbol in political_buys:
        score += 1
        reasons.append("Congress buy")

    if insider_news.get(symbol) == "positive":
        score += 1
        reasons.append("Insider news")

    tech = get_technical_signal(symbol)
    if tech == "buy":
        score += 1
        reasons.append("RSI < 30")
    elif tech == "sell":
        return None, []

    if score >= 2:
        return "buy", reasons
    return None, []
