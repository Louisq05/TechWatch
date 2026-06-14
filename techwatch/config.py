"""Tiny configuration helper.

Values are read from the environment first, then from a ``.env`` file at the
project root (simple ``key=value`` lines). The ``.env`` file is git-ignored, so
secrets such as the SMTP password never end up in the repository.
"""
import os

from .models.db import PROJECT_ROOT

_ENV_PATH = PROJECT_ROOT / ".env"
_file_cache = None


def _load_file():
    data = {}
    if _ENV_PATH.exists():
        for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def get(key, default=None):
    """Return a setting: environment wins, then .env, then `default`."""
    global _file_cache
    if _file_cache is None:
        _file_cache = _load_file()
    return os.environ.get(key) or _file_cache.get(key, default)
