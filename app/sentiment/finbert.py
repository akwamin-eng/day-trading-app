# app/sentiment/finbert.py

"""
FinBERT Sentiment Analyzer
Analyzes financial news sentiment using yiyanghkust/finbert-tone.
Correctly handles the model's label mapping: {0: 'Neutral', 1: 'Positive', 2: 'Negative'}
"""

import os
import logging
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Set up logging
logging.basicConfig(level=logging.INFO)

# Model configuration
MODEL_NAME = "yiyanghkust/finbert-tone"
MODEL_PATH = "app/sentiment/models/finbert"

# Global variables to cache model and tokenizer
_model = None
_tokenizer = None


def analyze_sentiment(text: str) -> dict:
    """
    Analyze financial sentiment of a given text using FinBERT.
    
    Args:
        text (str): Input financial news or statement
        
    Returns:
        dict: {
            "label": "Positive" | "Negative" | "Neutral",
            "score": float (confidence)
        }
    """
    global _model, _tokenizer

    # Validate input
    if not text or not isinstance(text, str) or len(text.strip()) == 0:
        logging.warning("⚠️ Empty or invalid text provided to analyze_sentiment")
        return {"label": "Neutral", "score": 0.0}

    # Lazy load model and tokenizer
    if _model is None or _tokenizer is None:
        try:
            if os.path.exists(MODEL_PATH):
                logging.info("✅ Loading FinBERT from local cache")
                _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
                _model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
            else:
                logging.info("📥 Downloading FinBERT from Hugging Face...")
                os.makedirs(MODEL_PATH, exist_ok=True)
                _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
                _model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
                _tokenizer.save_pretrained(MODEL_PATH)
                _model.save_pretrained(MODEL_PATH)
                logging.info("✅ FinBERT downloaded and cached")
        except Exception as e:
            logging.error(f"❌ Failed to load FinBERT model: {e}")
            return {"label": "Neutral", "score": 0.0}

    try:
        # Tokenize input
        inputs = _tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=False
        )

        # Run inference
        with torch.no_grad():
            outputs = _model(**inputs)
            logits = outputs.logits

        # Apply softmax to get probabilities
        probs = torch.nn.functional.softmax(logits, dim=-1)
        scores = probs[0].cpu().numpy()

        # Use the model's own label mapping
        id2label = _model.config.id2label  # {0: 'Neutral', 1: 'Positive', 2: 'Negative'}
        predicted_idx = scores.argmax()
        label = id2label[predicted_idx]
        confidence = float(scores[predicted_idx])

        return {"label": label, "score": confidence}

    except Exception as e:
        logging.error(f"❌ Error during sentiment analysis: {e}")
        return {"label": "Neutral", "score": 0.0}


# Test function (optional)
if __name__ == "__main__":
    # Test cases
    test_cases = [
        "Apple reports record earnings and raises guidance.",
        "Company files for bankruptcy after massive losses.",
        "Stock prices moved slightly today with no major news."
    ]

    for text in test_cases:
        result = analyze_sentiment(text)
        print(f"📝 {text}")
        print(f"📊 Sentiment: {result['label']} (Score: {result['score']:.3f})\n")
