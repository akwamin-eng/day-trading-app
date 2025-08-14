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
