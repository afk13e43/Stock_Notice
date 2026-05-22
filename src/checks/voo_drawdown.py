"""Check 4: VOO drawdown from all-time high — thresholds 10/20/30."""
from __future__ import annotations

from typing import Any

from src.data import yahoo
from src.state import drawdown_level, should_notify_ladder_drawdown

THRESHOLDS = [10, 20, 30]
STATE_KEY = "voo_drawdown_level"


def run(state: dict[str, Any]) -> str | None:
    df = yahoo.history("VOO", period="max").dropna(subset=["Close"])
    close = df["Close"]
    ath = close.cummax()
    dd_pct = float((1 - close.iloc[-1] / ath.iloc[-1]) * 100)
    current_level = drawdown_level(dd_pct, THRESHOLDS)
    stored = int(state.get(STATE_KEY, 0))

    state[STATE_KEY] = current_level

    if should_notify_ladder_drawdown(stored, current_level):
        date = df.index[-1].strftime("%Y-%m-%d")
        return (
            f"🚨 **VOO MDD 達 {dd_pct:.1f}%**（跨越 -{current_level}% 門檻）\n"
            f"收盤：{close.iloc[-1]:,.2f} / ATH：{ath.iloc[-1]:,.2f}\n"
            f"日期：{date}"
        )
    return None
