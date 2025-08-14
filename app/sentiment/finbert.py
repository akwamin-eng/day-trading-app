# app/sentiment/finbert.py

"""
FinBERT sentiment analyzer for financial news.
Loads model from local disk (not Hugging Face Hub).
"""

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax
import torch
import os

# Path to locally saved model
MODEL_DIR = "app/sentiment/models/finbert"

_tokenizer = None
_model = None


def load_finbert():
    """
    Lazily load FinBERT model and tokenizer from local disk.
    """
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        print("🧠 Loading FinBERT model from local path:", MODEL_DIR)

        if not os.path.exists(MODEL_DIR):
            raise FileNotFoundError(f"FinBERT model not found at {MODEL_DIR}. Did you run the download step?")

        # Load from local directory
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
        print("✅ FinBERT model loaded successfully.")

    return _tokenizer, _model


def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment of financial text.

    Returns:
        dict: {'positive': 0.1, 'negative': 0.8, 'neutral': 0.1, 'sentiment': 'negative', 'confidence': 0.8}
    """
    tokenizer, model = load_finbert()

    # Tokenize input
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    # Predict
    with torch.no_grad():
        outputs = model(**inputs)
        probabilities = softmax(outputs.logits, dim=-1).squeeze().tolist()

    # FinBERT labels: [negative, neutral, positive]
    labels = ['negative', 'neutral', 'positive']
    scores = {label: round(float(prob), 4) for label, prob in zip(labels, probabilities)}

    # Add dominant sentiment and confidence
    pos_neg_confidence = max(scores['positive'], scores['negative'])
    scores['sentiment'] = 'positive' if scores['positive'] > scores['negative'] else 'negative'
    scores['confidence'] = pos_neg_confidence

    return scores
