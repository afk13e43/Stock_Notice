"""Yahoo Finance data fetchers via yfinance."""
from __future__ import annotations

import sys

import pandas as pd
import yfinance as yf

# Realistic P/B band for large-cap equities. yfinance occasionally returns
# nonsense like 0.001 — anything outside this band is treated as bad data.
PB_SANE_RANGE = (0.2, 20.0)


def history(symbol: str, period: str = "max") -> pd.DataFrame:
    """Download full price history. Returns a DataFrame with at least 'Close'."""
    df = yf.download(symbol, period=period, progress=False, auto_adjust=False)
    if df is None or df.empty:
        raise RuntimeError(f"yfinance returned no data for {symbol}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def latest_close(symbol: str, period: str = "1mo") -> tuple[pd.Timestamp, float]:
    """Return (date, close) for the most recent trading day."""
    df = history(symbol, period=period)
    last = df.dropna(subset=["Close"]).iloc[-1]
    return last.name, float(last["Close"])


def get_pb_ratio(symbol: str) -> float | None:
    """Compute P/B = latest price / book value per share.

    Falls back to yfinance .info["priceToBook"] if direct calc isn't possible.
    Result is sanity-checked to PB_SANE_RANGE; anything outside returns None.
    yfinance's priceToBook field is known to be flaky (e.g. returning 0.001 for
    BRK.B), so we prefer the computed value.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
    except Exception as e:
        print(f"[yahoo] failed to fetch info for {symbol}: {e}", file=sys.stderr)
        return None

    price = _coerce_float(info.get("currentPrice")) or _coerce_float(info.get("regularMarketPrice"))
    if price is None:
        try:
            _, price = latest_close(symbol, period="5d")
        except Exception:
            price = None

    book_value_per_share = _coerce_float(info.get("bookValue"))

    computed: float | None = None
    if price and book_value_per_share and book_value_per_share > 0:
        computed = price / book_value_per_share

    reported = _coerce_float(info.get("priceToBook"))

    print(
        f"[yahoo] {symbol}: price={price} bookValue={book_value_per_share} "
        f"computed_pb={computed} reported_pb={reported}",
        file=sys.stderr,
    )

    for candidate in (computed, reported):
        if candidate is not None and PB_SANE_RANGE[0] <= candidate <= PB_SANE_RANGE[1]:
            return candidate

    print(
        f"[yahoo] {symbol}: no P/B value within sane range {PB_SANE_RANGE}",
        file=sys.stderr,
    )
    return None


def _coerce_float(v) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f
