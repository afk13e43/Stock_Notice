"""CSV history writer — append a new row per date, replace if same date exists."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def append_or_replace_row(path: Path, columns: list[str], row: dict[str, Any]) -> None:
    """Write `row` to CSV at `path` using `columns` as the header order.

    If a row with the same `date` already exists, replace it. Otherwise append.
    Missing keys in `row` are written as empty strings.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    date = row.get("date")
    if not date:
        raise ValueError("row must contain a 'date' key")

    existing: list[dict[str, str]] = []
    if path.exists():
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            existing = [r for r in reader]

    out_row = {col: _stringify(row.get(col)) for col in columns}

    replaced = False
    for i, r in enumerate(existing):
        if r.get("date") == date:
            existing[i] = out_row
            replaced = True
            break
    if not replaced:
        existing.append(out_row)

    existing.sort(key=lambda r: r.get("date", ""))

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(existing)


def _stringify(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        # Trim trailing zeros for cleaner CSVs; cap at 6 decimals.
        return f"{v:.6f}".rstrip("0").rstrip(".")
    return str(v)
