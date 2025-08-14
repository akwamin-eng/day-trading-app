# app/utils/config.py

"""
Central configuration loader.
"""

import yaml


def load_config():
    """
    Load configuration from config/config.yaml.

    Returns:
        dict: Configuration dictionary
    """
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)


# Global config object
_config = None


def get_config():
    """
    Get config (cached for performance).
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config

