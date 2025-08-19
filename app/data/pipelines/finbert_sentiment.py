# app/data/pipelines/finbert_sentiment.py

"""
FinBERT Sentiment Analyzer
Uses yiyanghkust/finbert-tone to analyze financial news and headlines.
Returns a sentiment score from -1.0 (negative) to +1.0 (positive).
"""

import logging
from transformers import pipeline
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

# Global variable to cache the pipeline
_sentiment_pipeline = None


def get_sentiment_pipeline():
    """
    Lazy-load the FinBERT sentiment pipeline.
    Ensures model is only loaded once, on first use.
    """
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        try:
            logging.info("🧠 Loading FinBERT sentiment model (yiyanghkust/finbert-tone)...")
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="yiyanghkust/finbert-tone",
                tokenizer="yiyanghkust/finbert-tone",
                device=-1,  # Use CPU (Cloud Run has no GPU)
                return_all_scores=False
            )
            logging.info("✅ FinBERT model loaded successfully")
        except Exception as e:
            logging.error(f"❌ Failed to load FinBERT model: {e}")
            raise
    return _sentiment_pipeline


def get_finbert_sentiment(text: str) -> float:
    """
    Analyze financial text and return a sentiment score.
    
    Args:
        text (str): News headline, SEC filing excerpt, or social media post
        
    Returns:
        float: Score from -1.0 (bearish) to +1.0 (bullish)
               Returns 0.0 if input is empty or model fails
    """
    if not text or not text.strip():
        logging.debug("⚠️ Empty text input for sentiment analysis")
        return 0.0

    try:
        # Truncate to model's max length (512 tokens)
        truncated = text.strip()[:510]

        # Get prediction
        pipeline = get_sentiment_pipeline()
        result = pipeline(truncated)[0]

        # Convert to signed score
        score = result["score"]
        if result["label"] == "Positive":
            return score
        elif result["label"] == "Negative":
            return -score
        else:
            return 0.0  # Neutral (rare)

    except Exception as e:
        logging.error(f"❌ FinBERT sentiment analysis failed for text: {text[:100]}... | Error: {e}")
        return 0.0


# --- Example Usage ---
if __name__ == "__main__":
    sample_headlines = [
        "Rep. Johnson buys $100,000 worth of RARE stock after favorable committee vote",
        "RARE misses Q2 earnings expectations, revenue down 12% year-over-year",
        "FDA grants fast-track designation to RARE Therapeutics' new drug candidate",
        "Insider selling spikes at RARE — CFO sells $2M in shares",
        "Congressional committee approves new energy bill, boosting clean tech stocks"
    ]

    for headline in sample_headlines:
        score = get_finbert_sentiment(headline)
        if score > 0.3:
            sentiment = "📈 Strong Bullish"
        elif score > 0.1:
            sentiment = "📈 Mild Bullish"
        elif score < -0.3:
            sentiment = "📉 Strong Bearish"
        elif score < -0.1:
            sentiment = "📉 Mild Bearish"
        else:
            sentiment = "⚖️ Neutral"
        print(f"{sentiment} | {score:.3f} | {headline}")
