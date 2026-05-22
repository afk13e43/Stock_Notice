"""Check 5: BRK.B P/B ratio — thresholds 1.35 / 1.30 / 1.25 / 1.20."""
from __future__ import annotations

from typing import Any

from src.data import yahoo
from src.state import pb_level, should_notify_ladder_pb

THRESHOLDS = [1.35, 1.30, 1.25, 1.20]
STATE_KEY = "brkb_pb_level"


def run(state: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    # Query BRK-A: yfinance returns BRK-A's per-share book value for both classes,
    # so BRK-B's reported bookValue is wrong (off by ~1500x). P/B is identical
    # across share classes since A and B are economically proportional.
    pb = yahoo.get_pb_ratio("BRK-A")
    if pb is None:
        return None, {}

    current_level = pb_level(pb, THRESHOLDS)
    stored_raw = state.get(STATE_KEY)
    stored: float | None = float(stored_raw) if stored_raw is not None else None

    state[STATE_KEY] = current_level

    metrics = {"brkb_pb_ratio": pb}

    msg = None
    if should_notify_ladder_pb(stored, current_level):
        msg = f"🚨 **BRK.B P/B 跌至 {pb:.3f}**（跨越 {current_level} 門檻）"
    return msg, metrics
