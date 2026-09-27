from __future__ import annotations

"""Compatibility package for tests.

Tests expect:
  from logger.logger import get_logger

The implementation lives in this repo as a flat module `logger.py`.

To avoid import recursion issues (this package is also named `logger`),
we load `logger.py` under a temporary alias and re-export `get_logger`.
"""

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_flat_logger_path = _ROOT / "logger.py"

_spec = importlib.util.spec_from_file_location("_flat_logger", _flat_logger_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load flat logger module from {_flat_logger_path}")

_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

get_logger = _mod.get_logger



