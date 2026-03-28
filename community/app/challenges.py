"""Load weekly challenges from JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_challenges: list[dict[str, Any]] = []


def load_challenges(path: str) -> list[dict[str, Any]]:
    """Load challenges from a JSON file and cache them in module state."""
    global _challenges  # noqa: PLW0603
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    _challenges = list(data)
    return _challenges


def get_challenges() -> list[dict[str, Any]]:
    """Return the loaded challenges list."""
    return _challenges
