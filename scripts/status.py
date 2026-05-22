"""Print current values for all 6 monitored metrics. Read-only, sends no notifications."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import yahoo, twse  # noqa: E402


def fmt(v, suffix: str = "", fmt_spec: str = ",.2f") -> str:
    if v is None:
        return "—"
    try:
        return f"{v:{fmt_spec}}{suffix}"
    except (TypeError, ValueError):
        return str(v)


def main() -> None:
    print("=" * 60)
    print("Stock Notice — current status")
    print("=" * 60)

    # 1+2. TAIEX
    try:
        df = yahoo.history("^TWII", period="max").dropna(subset=["Close"])
        close = df["Close"]
        ath = close.cummax()
        dd = float((1 - close.iloc[-1] / ath.iloc[-1]) * 100)
        ma240 = close.rolling(240).mean().iloc[-1]
        date = df.index[-1].strftime("%Y-%m-%d")
        last = float(close.iloc[-1])
        print(f"\n[1] 台股回檔  ({date})")
        print(f"    收盤={fmt(last)} / ATH={fmt(float(ath.iloc[-1]))} / DD={fmt(dd, '%')}")
        print(f"    門檻 10/20/30 → 目前 {'已跨越 -%d%%' % _level(dd, [10,20,30]) if _level(dd,[10,20,30]) else '未觸發'}")
        print(f"\n[2] 台股 MA240")
        print(f"    收盤={fmt(last)} / MA240={fmt(float(ma240))} / diff={fmt((last/ma240 - 1)*100, '%')}")
        print(f"    {'⚠️ 已跌破 MA240' if last < ma240 else '✓ 未跌破'}")
    except Exception as e:
        print(f"\n[1+2] TAIEX 失敗: {e}")

    # 3. Taiwan margin maintenance ratio
    try:
        ratio = twse.fetch_overall_margin_maintenance_ratio()
        print(f"\n[3] 台股整體融資維持率")
        print(f"    維持率={fmt(ratio, '%')} / 門檻 135%")
        if ratio is not None:
            print(f"    {'⚠️ 已跌破' if ratio < 135 else '✓ 未跌破'}")
    except Exception as e:
        print(f"\n[3] 維持率 失敗: {e}")

    # 4. VOO drawdown
    try:
        df = yahoo.history("VOO", period="max").dropna(subset=["Close"])
        close = df["Close"]
        ath = close.cummax()
        dd = float((1 - close.iloc[-1] / ath.iloc[-1]) * 100)
        date = df.index[-1].strftime("%Y-%m-%d")
        print(f"\n[4] VOO 回檔  ({date})")
        print(f"    收盤={fmt(float(close.iloc[-1]))} / ATH={fmt(float(ath.iloc[-1]))} / DD={fmt(dd, '%')}")
        print(f"    門檻 10/20/30 → 目前 {'已跨越 -%d%%' % _level(dd, [10,20,30]) if _level(dd,[10,20,30]) else '未觸發'}")
    except Exception as e:
        print(f"\n[4] VOO 失敗: {e}")

    # 5. BRK.B P/B  (query BRK-A — see comment in src/checks/brkb_pb.py)
    try:
        pb = yahoo.get_pb_ratio("BRK-A")
        print(f"\n[5] BRK.B P/B")
        print(f"    P/B={fmt(pb, '', '.3f')}")
        if pb is not None:
            lvl = _pb_level(pb, [1.35, 1.30, 1.25, 1.20])
            print(f"    門檻 1.35/1.30/1.25/1.20 → 目前 {('已跨越 ' + str(lvl)) if lvl else '未觸發'}")
    except Exception as e:
        print(f"\n[5] BRK.B P/B 失敗: {e}")

    # 6. USD/TWD
    try:
        date, last = yahoo.latest_close("TWD=X", period="5d")
        print(f"\n[6] USD/TWD  ({date.strftime('%Y-%m-%d')})")
        print(f"    匯率={fmt(last, '', '.4f')} / 門檻 30")
        print(f"    {'⚠️ 已低於 30' if last < 30 else '✓ 未觸發'}")
    except Exception as e:
        print(f"\n[6] USD/TWD 失敗: {e}")

    print("\n" + "=" * 60)


def _level(dd: float, thresholds: list[int]) -> int:
    lvl = 0
    for t in thresholds:
        if dd >= t:
            lvl = t
    return lvl


def _pb_level(pb: float, thresholds: list[float]):
    sorted_desc = sorted(thresholds, reverse=True)
    lvl = None
    for t in sorted_desc:
        if pb <= t:
            lvl = t
    return lvl


if __name__ == "__main__":
    main()
