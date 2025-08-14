# app/utils/secrets.py

"""
Securely fetch secrets from GCP Secret Manager.
"""

from google.cloud import secretmanager
import os


def access_secret(project_id, secret_id, version_id="latest"):
    """
    Access a secret from GCP Secret Manager.

    Args:
        project_id (str): GCP project ID
        secret_id (str): Secret name (e.g., 'alpaca-api-key')
        version_id (str): Version (default: 'latest')

    Returns:
        str: Decoded secret value
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    try:
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        raise RuntimeError(f"Failed to access secret {secret_id}: {e}")


def get_alpaca_keys():
    """
    Get Alpaca API and secret keys.

    Returns:
        dict: {'api_key': str, 'secret_key': str}
    """
    project_id = "day-trading-app-468901"  # Hardcoded for now (or load from config)
    api_key = access_secret(project_id, "alpaca-api-key")
    secret_key = access_secret(project_id, "alpaca-secret-key")
    return {
        "api_key": api_key,
        "secret_key": secret_key
    }

def get_newsapi_key():
    project_id = "day-trading-app-468901"
    key = access_secret(project_id, "newsapi-key")
    return key.strip()  # Removes any accidental whitespace or newlines

def get_tiingo_api_token():
    project_id = "day-trading-app-468901"
    token = access_secret(project_id, "tiingo-api-token")
    return token.strip()  # Defensive: remove any whitespace/newlines

def get_alphavantage_key():
    """
    Get Alpha Vantage API key from Secret Manager.
    """
    project_id = "day-trading-app-468901"
    return access_secret(project_id, "alphavantage-key").strip()

def get_paper_api_key():
    project_id = "day-trading-app-468901"
    return access_secret(project_id, "alpaca-paper-api-key").strip()

def get_paper_secret_key():
    project_id = "day-trading-app-468901"
    return access_secret(project_id, "alpaca-paper-secret-key").strip()
