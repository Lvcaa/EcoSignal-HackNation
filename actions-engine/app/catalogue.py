"""Loads and exposes the action catalogue. No FastAPI imports."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas import ActionItem

ACTIONS: list[ActionItem] = []


def load_catalogue(path: str = "catalogue.json") -> list[ActionItem]:
    """Read catalogue.json and parse entries as ActionItem. Called once at startup."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    items = [ActionItem.model_validate(entry) for entry in raw]
    ACTIONS.clear()
    ACTIONS.extend(items)
    return items


def get_action_by_id(action_id: str) -> ActionItem | None:
    """Linear search through ACTIONS. Returns None if not found."""
    for action in ACTIONS:
        if action.action_id == action_id:
            return action
    return None


def get_all_actions() -> list[ActionItem]:
    """Returns a copy of the ACTIONS list."""
    return list(ACTIONS)
