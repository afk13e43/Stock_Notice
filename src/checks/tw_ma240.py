"""Check 2: TAIEX (^TWII) closes below MA240."""
from __future__ import annotations

from typing import Any

from src.data import yahoo
from src.state import should_notify_bool

STATE_KEY = "tw_below_ma240"


def run(state: dict[str, Any]) -> str | None:
    df = yahoo.history("^TWII", period="max").dropna(subset=["Close"])
    if len(df) < 240:
        return None
    close = df["Close"]
    ma240 = close.rolling(240).mean()
    last_close = float(close.iloc[-1])
    last_ma = float(ma240.iloc[-1])
    below = last_close < last_ma

    stored = bool(state.get(STATE_KEY, False))
    state[STATE_KEY] = below

    if should_notify_bool(stored, below):
        date = df.index[-1].strftime("%Y-%m-%d")
        diff_pct = (last_close / last_ma - 1) * 100
        return (
            f"⚠️ **台股大盤跌破 MA240**\n"
            f"收盤：{last_close:,.2f} / MA240：{last_ma:,.2f}（{diff_pct:+.2f}%）\n"
            f"日期：{date}"
        )
    return None
