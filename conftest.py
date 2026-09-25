"""Pytest configuration.

This repo’s Python sources currently live as top-level modules (e.g. tweet_formatter.py)
while the tests expect importable packages named `formatter` and `twitter`.

This conftest adds the project root to sys.path and provides lightweight
package aliases so tests can import:
  - from formatter.tweet_formatter import TweetFormatter
  - from twitter.twitter_client import TwitterClient
"""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    # Make top-level modules (tweet_formatter.py, twitter_client.py, etc.) importable.
    sys.path.insert(0, str(ROOT))


def _alias_package(package_name: str, module_name: str, submodule_name: str) -> None:
    """Create an import alias: `package_name.submodule_name` -> import(module_name)."""

    # If something already placed a non-package module into sys.modules,
    # do not reuse it; overwrite with a package stub.
    pkg = sys.modules.get(package_name)
    if pkg is None or not hasattr(pkg, "__path__"):
        pkg = types.ModuleType(package_name)
        pkg.__path__ = []  # mark as namespace-ish package
        sys.modules[package_name] = pkg

    submod_fullname = f"{package_name}.{submodule_name}"

    # Import the target module first.
    target = importlib.import_module(module_name)

    # Register the nested import path.
    sys.modules[submod_fullname] = target

    # Also expose as an attribute on the package (some import styles rely on this).
    setattr(pkg, submodule_name, target)





# Create package-like aliases that also support nested imports.
# Note: we already have a real `logger/` compatibility package in this repo,
# so we do NOT alias `logger` here to avoid import shadowing issues.







# formatter.tweet_formatter -> tweet_formatter.py
_alias_package("formatter", "tweet_formatter", "tweet_formatter")

# twitter.twitter_client -> twitter_client.py
_alias_package("twitter", "twitter_client", "twitter_client")



