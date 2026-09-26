"""
helpers.py
Shared utility functions.
"""

import os
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "config.yaml"


def get_env_or_raise(key: str) -> str:
    """Return the value of an env var, raising a clear error if missing."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Add it to your .env file or GitHub Secrets."
        )
    return value


def load_config(path: Path = CONFIG_PATH) -> dict:
    """
    Load YAML config. Returns an empty dict if the file doesn't exist,
    so the app runs with sensible defaults even without a config file.
    """
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def truncate(text: str, max_len: int, suffix: str = "…") -> str:
    """Truncate text to max_len characters, appending suffix if cut."""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix
