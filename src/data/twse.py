"""TWSE data fetchers — OpenAPI + one legacy endpoint for the daily total loan."""
from __future__ import annotations

import sys

import requests

# OpenAPI: per-stock margin balance (融資今日餘額 in 張)
MARGIN_PER_STOCK_URL = "https://openapi.twse.com.tw/v1/exchangeReport/MI_MARGN"
# OpenAPI: all stocks daily summary (含 ClosingPrice)
STOCK_DAY_ALL_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
# Legacy: market-wide margin summary, gives 融資金額(仟元) 今日餘額
MARGIN_TOTAL_URL = "https://www.twse.com.tw/exchangeReport/MI_MARGN"

# 張 to shares for TWSE listed stocks. Standard board lot.
SHARES_PER_LOT = 1000


def fetch_overall_margin_maintenance_ratio() -> float | None:
    """Compute TWSE-listed overall margin maintenance ratio (%) from raw TWSE data.

    維持率 = (Σ 每檔融資餘額張數 × 1000 × 當日收盤價) / 整體融資金額餘額 × 100

    Returns None on holidays / API errors. Prints diagnostics to stderr.
    """
    per_stock = _fetch_per_stock_margin()
    closes = _fetch_all_stock_closes()
    total_loan_ntd = _fetch_total_margin_loan_ntd()

    if not per_stock:
        print("[twse] per-stock margin data empty", file=sys.stderr)
        return None
    if not closes:
        print("[twse] per-stock closes data empty", file=sys.stderr)
        return None
    if not total_loan_ntd or total_loan_ntd <= 0:
        print("[twse] total margin loan unavailable", file=sys.stderr)
        return None

    matched = 0
    unmatched = 0
    collateral_value = 0.0
    for code, lots in per_stock.items():
        close = closes.get(code)
        if close is None or lots <= 0:
            unmatched += 1
            continue
        collateral_value += lots * SHARES_PER_LOT * close
        matched += 1

    if collateral_value <= 0:
        print("[twse] computed collateral value is 0", file=sys.stderr)
        return None

    ratio = collateral_value / total_loan_ntd * 100
    print(
        f"[twse] matched={matched} unmatched={unmatched} "
        f"collateral={collateral_value:,.0f} loan={total_loan_ntd:,.0f} ratio={ratio:.2f}%",
        file=sys.stderr,
    )
    return ratio


def _fetch_per_stock_margin() -> dict[str, float]:
    """Return {Code: 融資今日餘額(張)} from TWSE OpenAPI."""
    resp = requests.get(MARGIN_PER_STOCK_URL, timeout=20)
    resp.raise_for_status()
    rows = resp.json() or []
    out: dict[str, float] = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        code = r.get("股票代號")
        lots = _to_float(r.get("融資今日餘額"))
        if code and lots is not None:
            out[str(code).strip()] = lots
    return out


def _fetch_all_stock_closes() -> dict[str, float]:
    """Return {Code: ClosingPrice} from TWSE OpenAPI."""
    resp = requests.get(STOCK_DAY_ALL_URL, timeout=20)
    resp.raise_for_status()
    rows = resp.json() or []
    out: dict[str, float] = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        code = r.get("Code")
        close = _to_float(r.get("ClosingPrice"))
        if code and close is not None:
            out[str(code).strip()] = close
    return out


def _fetch_total_margin_loan_ntd() -> float | None:
    """Fetch market-wide margin loan amount in NTD from the legacy MS endpoint.

    The legacy URL returns a 'tables' array; the maintenance summary contains a row
    titled '融資金額(仟元)' whose '今日餘額' column is the total margin loan in 千元.
    """
    # No `date` param → endpoint returns the most recent published date.
    url = f"{MARGIN_TOTAL_URL}?response=json&selectType=MS"
    resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("stat") != "OK":
        return None

    for table in payload.get("tables", []):
        fields = table.get("fields") or []
        data = table.get("data") or []
        if "今日餘額" not in fields:
            continue
        balance_idx = fields.index("今日餘額")
        for row in data:
            if not row:
                continue
            label = str(row[0])
            if "融資金額" in label:  # row "融資金額(仟元)"
                amount_thousands = _to_float(row[balance_idx])
                if amount_thousands is None:
                    return None
                return amount_thousands * 1000  # 仟元 → NTD
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
