"""TWSE OpenAPI fetchers."""
from __future__ import annotations

import requests

MARGIN_URL = "https://openapi.twse.com.tw/v1/exchangeReport/MI_MARGN"


def fetch_overall_margin_maintenance_ratio() -> float | None:
    """Return the overall market margin maintenance ratio in percent (e.g. 158.3)
    for the latest trading day, or None on holidays / when unavailable.

    The TWSE OpenAPI returns a list of rows for the day's margin/short summary.
    The row keyed by "整體市場" / "Total" carries the maintenance ratio under
    a key like "整體市場融資維持率(%)". Field naming has shifted in the past,
    so we scan flexibly.
    """
    resp = requests.get(MARGIN_URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return None

    target_keywords = ("維持率",)

    # Strategy 1: a flat dict with a maintenance-ratio key (some endpoints return this)
    if isinstance(data, dict):
        for k, v in data.items():
            if any(kw in k for kw in target_keywords):
                return _to_float(v)

    # Strategy 2: list of rows — find the "整體市場" / "Total" row and its 維持率 column
    if isinstance(data, list):
        for row in data:
            if not isinstance(row, dict):
                continue
            label = " ".join(str(v) for v in row.values() if isinstance(v, str))
            if "整體" in label or "Total" in label:
                for k, v in row.items():
                    if any(kw in k for kw in target_keywords):
                        ratio = _to_float(v)
                        if ratio is not None:
                            return ratio
        # Fallback: any row with a 維持率 field at all
        for row in data:
            if not isinstance(row, dict):
                continue
            for k, v in row.items():
                if any(kw in k for kw in target_keywords):
                    ratio = _to_float(v)
                    if ratio is not None:
                        return ratio

    return None


def _to_float(v) -> float | None:
    if v is None:
        return None
    s = str(v).replace(",", "").replace("%", "").strip()
    if not s or s in ("-", "--"):
        return None
    try:
        return float(s)
    except ValueError:
        return None
