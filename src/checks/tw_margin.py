"""Check 3: Taiwan overall margin maintenance ratio falls below 135%."""
from __future__ import annotations

from typing import Any

from src.data import twse
from src.state import should_notify_bool

THRESHOLD = 135.0
STATE_KEY = "tw_margin_below_135"


def run(state: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    ratio = twse.fetch_overall_margin_maintenance_ratio()
    if ratio is None:
        return None, {}

    below = ratio < THRESHOLD
    stored = bool(state.get(STATE_KEY, False))
    state[STATE_KEY] = below

    metrics = {"margin_ratio_pct": ratio}

    msg = None
    if should_notify_bool(stored, below):
        msg = (
            f"🚨 **台股融資維持率跌破 {THRESHOLD:.0f}%**\n"
            f"目前整體市場融資維持率：{ratio:.2f}%"
        )
    return msg, metrics
