"""Check 3: Taiwan overall margin maintenance ratio falls below 135%."""
from __future__ import annotations

from typing import Any

from src.data import twse
from src.state import should_notify_bool

THRESHOLD = 135.0
STATE_KEY = "tw_margin_below_135"


def run(state: dict[str, Any]) -> str | None:
    ratio = twse.fetch_overall_margin_maintenance_ratio()
    if ratio is None:
        # TWSE returned nothing (holiday) — leave state alone.
        return None

    below = ratio < THRESHOLD
    stored = bool(state.get(STATE_KEY, False))
    state[STATE_KEY] = below

    if should_notify_bool(stored, below):
        return (
            f"🚨 **台股融資維持率跌破 {THRESHOLD:.0f}%**\n"
            f"目前整體市場融資維持率：{ratio:.2f}%"
        )
    return None
