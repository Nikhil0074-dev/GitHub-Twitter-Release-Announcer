"""Compatibility wrapper.

Tests import:
  from logger.logger import get_logger

Implementation lives in top-level `logger.py`.
"""

# Import directly from the repo's top-level module.
# (The conftest in this repo manages sys.path so this works under pytest.)
from logger import get_logger  # type: ignore

