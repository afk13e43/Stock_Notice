"""Check 5: BRK.B P/B ratio — thresholds 1.35 / 1.30 / 1.25 / 1.20."""
from __future__ import annotations

from typing import Any

from src.data import yahoo
from src.state import pb_level, should_notify_ladder_pb

THRESHOLDS = [1.35, 1.30, 1.25, 1.20]
STATE_KEY = "brkb_pb_level"


def run(state: dict[str, Any]) -> str | None:
    pb = yahoo.get_pb_ratio("BRK-B")
    if pb is None:
        # Could not fetch P/B — leave state alone, do not notify.
        return None

    current_level = pb_level(pb, THRESHOLDS)
    stored_raw = state.get(STATE_KEY)
    stored: float | None = float(stored_raw) if stored_raw is not None else None

    state[STATE_KEY] = current_level

    if should_notify_ladder_pb(stored, current_level):
        return (
            f"🚨 **BRK.B P/B 跌至 {pb:.3f}**（跨越 {current_level} 門檻）"
        )
    return None
