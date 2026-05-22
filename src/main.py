"""Entry point: python -m src.main --market {tw|us}."""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from src import history, notifier, state
from src.checks import (
    brkb_pb,
    tw_drawdown,
    tw_ma240,
    tw_margin,
    usdtwd,
    voo_drawdown,
)

TW_CHECKS = [
    ("tw_drawdown", tw_drawdown.run),
    ("tw_ma240", tw_ma240.run),
    ("tw_margin", tw_margin.run),
    ("usdtwd", usdtwd.run),
]
US_CHECKS = [
    ("voo_drawdown", voo_drawdown.run),
    ("brkb_pb", brkb_pb.run),
]

STATE_FILES = {
    "tw": Path("state/tw_state.json"),
    "us": Path("state/us_state.json"),
}

HISTORY_FILES = {
    "tw": Path("history/tw_history.csv"),
    "us": Path("history/us_history.csv"),
}

HISTORY_COLUMNS = {
    "tw": [
        "date",
        "twii_close",
        "twii_ath",
        "twii_drawdown_pct",
        "twii_ma240",
        "twii_below_ma240",
        "margin_ratio_pct",
        "usdtwd_rate",
    ],
    "us": [
        "date",
        "voo_close",
        "voo_ath",
        "voo_drawdown_pct",
        "brkb_pb_ratio",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", choices=["tw", "us"], required=True)
    args = parser.parse_args()

    checks = TW_CHECKS if args.market == "tw" else US_CHECKS
    state_path = STATE_FILES[args.market]
    history_path = HISTORY_FILES[args.market]
    columns = HISTORY_COLUMNS[args.market]
    st = state.load_state(state_path)

    messages: list[str] = []
    errors: list[str] = []
    row: dict[str, object] = {}

    for name, fn in checks:
        try:
            msg, metrics = fn(st)
        except Exception as exc:
            errors.append(f"[{name}] {type(exc).__name__}: {exc}")
            traceback.print_exc()
            continue
        row.update(metrics)
        if msg:
            print(f"[{name}] would notify:\n{msg}\n")
            messages.append(msg)
        else:
            print(f"[{name}] no change.")

    if errors:
        messages.append("⚠️ 抓取錯誤：\n" + "\n".join(errors))

    notifier.send(messages)
    state.save_state(state_path, st)

    if row.get("date"):
        history.append_or_replace_row(history_path, columns, row)
        print(f"History written to {history_path}.")
    else:
        print("No date in collected metrics — skipping history write.")

    print(f"Done. Notified {len(messages)} message(s). State written to {state_path}.")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
