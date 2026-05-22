"""Entry point: python -m src.main --market {tw|us}."""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from src import notifier, state
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", choices=["tw", "us"], required=True)
    args = parser.parse_args()

    checks = TW_CHECKS if args.market == "tw" else US_CHECKS
    state_path = STATE_FILES[args.market]
    st = state.load_state(state_path)

    messages: list[str] = []
    errors: list[str] = []

    for name, fn in checks:
        try:
            msg = fn(st)
        except Exception as exc:
            errors.append(f"[{name}] {type(exc).__name__}: {exc}")
            traceback.print_exc()
            continue
        if msg:
            print(f"[{name}] would notify:\n{msg}\n")
            messages.append(msg)
        else:
            print(f"[{name}] no change.")

    if errors:
        # Surface errors to Discord too, so silent failures don't accumulate.
        messages.append("⚠️ 抓取錯誤：\n" + "\n".join(errors))

    notifier.send(messages)
    state.save_state(state_path, st)

    print(f"Done. Notified {len(messages)} message(s). State written to {state_path}.")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
