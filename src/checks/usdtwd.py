"""Check 6: USD/TWD exchange rate falls below 30."""
from __future__ import annotations

from typing import Any

from src.data import yahoo
from src.state import should_notify_bool

THRESHOLD = 30.0
STATE_KEY = "usdtwd_below_30"


def run(state: dict[str, Any]) -> str | None:
    date, rate = yahoo.latest_close("TWD=X", period="1mo")
    below = rate < THRESHOLD
    stored = bool(state.get(STATE_KEY, False))
    state[STATE_KEY] = below

    if should_notify_bool(stored, below):
        return (
            f"💱 **美元兌台幣跌破 {THRESHOLD:.0f}**\n"
            f"目前匯率：{rate:.4f}\n"
            f"日期：{date.strftime('%Y-%m-%d')}"
        )
    return None
