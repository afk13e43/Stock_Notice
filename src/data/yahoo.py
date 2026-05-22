"""Yahoo Finance data fetchers via yfinance."""
from __future__ import annotations

import pandas as pd
import yfinance as yf


def history(symbol: str, period: str = "max") -> pd.DataFrame:
    """Download full price history. Returns a DataFrame with at least 'Close'."""
    df = yf.download(symbol, period=period, progress=False, auto_adjust=False)
    if df is None or df.empty:
        raise RuntimeError(f"yfinance returned no data for {symbol}")
    # yfinance may return columns as a MultiIndex when a single symbol is passed.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def latest_close(symbol: str, period: str = "1mo") -> tuple[pd.Timestamp, float]:
    """Return (date, close) for the most recent trading day."""
    df = history(symbol, period=period)
    last = df.dropna(subset=["Close"]).iloc[-1]
    return last.name, float(last["Close"])


def get_pb_ratio(symbol: str) -> float | None:
    """Best-effort priceToBook from yfinance .info — None if unavailable."""
    try:
        info = yf.Ticker(symbol).info
    except Exception:
        return None
    pb = info.get("priceToBook")
    if pb is None:
        return None
    try:
        pb = float(pb)
    except (TypeError, ValueError):
        return None
    if pb <= 0:
        return None
    return pb
