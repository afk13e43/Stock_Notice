"""State persistence + threshold-crossing helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    return json.loads(text)


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def drawdown_level(dd_pct: float, thresholds: list[int]) -> int:
    """Given a drawdown as positive percent (e.g. 22.3 for -22.3%),
    return the highest threshold it has crossed. 0 if none.

    thresholds: ascending list of positive ints, e.g. [10, 20, 30].
    """
    level = 0
    for t in thresholds:
        if dd_pct >= t:
            level = t
    return level


def pb_level(pb: float, thresholds: list[float]) -> float | None:
    """For a "lower is more severe" ladder like [1.35, 1.30, 1.25, 1.20]:
    return the lowest threshold that the value has crossed below.
    None if not even the highest threshold is crossed.
    """
    sorted_desc = sorted(thresholds, reverse=True)
    level: float | None = None
    for t in sorted_desc:
        if pb <= t:
            level = t
    return level


def should_notify_ladder_drawdown(stored: int, current: int) -> bool:
    """For drawdown ladders: only notify when escalating to a worse level."""
    return current > stored


def should_notify_ladder_pb(stored: float | None, current: float | None) -> bool:
    """For P/B ladder: notify when current is a *lower* (worse) threshold than stored."""
    if current is None:
        return False
    if stored is None:
        return True
    return current < stored


def should_notify_bool(stored: bool, current: bool) -> bool:
    """Notify only on false -> true transitions."""
    return current and not stored
