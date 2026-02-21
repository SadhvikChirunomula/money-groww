"""
Technical indicators: SMA, EMA, daily returns, cumulative returns, stats.
"""

import pandas as pd
import numpy as np


def add_sma(
    df: pd.DataFrame, column: str = "Close", windows: list[int] | None = None
) -> pd.DataFrame:
    """Add Simple Moving Average columns to *df*."""
    if windows is None:
        windows = [20, 50, 200]
    result = df.copy()
    for w in windows:
        result[f"SMA_{w}"] = result[column].rolling(window=w).mean()
    return result


def add_ema(
    df: pd.DataFrame, column: str = "Close", windows: list[int] | None = None
) -> pd.DataFrame:
    """Add Exponential Moving Average columns to *df*."""
    if windows is None:
        windows = [12, 26, 50]
    result = df.copy()
    for w in windows:
        result[f"EMA_{w}"] = result[column].ewm(span=w, adjust=False).mean()
    return result


def compute_daily_returns(df: pd.DataFrame, column: str = "Close") -> pd.Series:
    """Daily percentage returns."""
    return df[column].pct_change() * 100


def compute_cumulative_returns(
    df: pd.DataFrame, column: str = "Close"
) -> pd.Series:
    """Cumulative returns from the start of the series."""
    return (df[column] / df[column].iloc[0] - 1) * 100


def compute_volatility(
    df: pd.DataFrame, column: str = "Close", window: int = 30
) -> pd.Series:
    """Rolling annualised volatility."""
    daily_returns = df[column].pct_change()
    return daily_returns.rolling(window=window).std() * np.sqrt(252) * 100


def compute_stats(df: pd.DataFrame, column: str = "Close") -> dict:
    """Compute summary statistics for a stock."""
    prices = df[column].dropna()
    daily_returns = prices.pct_change().dropna()

    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
    annualized_vol = daily_returns.std() * np.sqrt(252) * 100
    max_drawdown = ((prices / prices.cummax()) - 1).min() * 100

    years = (prices.index[-1] - prices.index[0]).days / 365.25
    cagr = (
        ((prices.iloc[-1] / prices.iloc[0]) ** (1 / years) - 1) * 100
        if years > 0
        else 0
    )

    tail_252 = prices.tail(252) if len(prices) >= 252 else prices

    return {
        "Total Return (%)": round(total_return, 2),
        "CAGR (%)": round(cagr, 2),
        "Annualized Volatility (%)": round(annualized_vol, 2),
        "Max Drawdown (%)": round(max_drawdown, 2),
        "Current Price": round(prices.iloc[-1], 2),
        "52-Wk High": round(tail_252.max(), 2),
        "52-Wk Low": round(tail_252.min(), 2),
    }
