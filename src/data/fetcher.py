"""
Stock data fetching module using yfinance.
"""

import yfinance as yf
import pandas as pd
import streamlit as st
from src.config import POPULAR_TICKERS


def search_tickers(query: str) -> list[tuple[str, str]]:
    """
    Search Yahoo Finance for tickers matching *query*.

    Returns a list of ``(display_label, symbol)`` tuples filtered to Indian
    NSE stocks (``.NS`` suffix).  Falls back to matching entries from
    ``POPULAR_TICKERS`` when the API returns nothing.
    """
    if not query or len(query) < 1:
        return []

    results: list[tuple[str, str]] = []

    # ── Yahoo Finance search API via yfinance ────────────────────
    try:
        search = yf.Search(query, max_results=10)
        for q in search.quotes or []:
            symbol = q.get("symbol", "")
            name = q.get("shortname") or q.get("longname") or symbol
            exchange = q.get("exchDisp", "")
            # Only keep NSE stocks
            if symbol.endswith(".NS"):
                label = f"{symbol.replace('.NS', '')} — {name}  ({exchange})"
                results.append((label, symbol))
    except Exception:
        pass

    # ── Fallback: match against the built-in POPULAR_TICKERS list ─
    if not results:
        q_upper = query.strip().upper()
        for _cat, tickers in POPULAR_TICKERS.items():
            for t in tickers:
                if q_upper in t.upper().replace(".NS", ""):
                    label = t.replace(".NS", "")
                    results.append((label, t))

    # Deduplicate keeping order
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for label, sym in results:
        if sym not in seen:
            seen.add(sym)
            unique.append((label, sym))
    return unique


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_stock_data(
    ticker: str, period: str = "1y", interval: str = "1d"
) -> pd.DataFrame:
    """
    Fetch historical stock data from Yahoo Finance.

    Args:
        ticker: Stock ticker symbol (e.g. ``RELIANCE.NS``, ``TCS.NS``)
        period: ``1mo | 3mo | 6mo | 1y | 2y | 5y | 10y | max``
        interval: ``1d | 1wk | 1mo``

    Returns:
        DataFrame with OHLCV columns.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        df.index = df.index.tz_localize(None)
        return df
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_stock_data_by_dates(
    ticker: str, start: str, end: str, interval: str = "1d"
) -> pd.DataFrame:
    """Fetch historical stock data between specific dates."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start, end=end, interval=interval)
        if df.empty:
            return pd.DataFrame()
        df.index = df.index.tz_localize(None)
        return df
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_stock_info(ticker: str) -> dict:
    """
    Get stock metadata (name, sector, market cap, etc.).
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "currency": info.get("currency", "INR"),
            "exchange": info.get("exchange", "N/A"),
            "summary": info.get(
                "longBusinessSummary", "No description available."
            ),
        }
    except Exception:
        return {
            "name": ticker,
            "sector": "N/A",
            "industry": "N/A",
            "market_cap": 0,
            "currency": "INR",
            "exchange": "N/A",
            "summary": "No description available.",
        }
