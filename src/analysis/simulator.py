"""
Investment simulation: lump-sum and SIP (Systematic Investment Plan).
"""

import pandas as pd


def simulate_investment(
    df: pd.DataFrame, initial_amount: float, column: str = "Close"
) -> pd.DataFrame:
    """
    Simulate lump-sum investment growth over time.

    Args:
        df: OHLCV DataFrame.
        initial_amount: Amount invested at the start (₹).
        column: Price column to use.

    Returns:
        DataFrame with Portfolio_Value, Gain_Loss, Return_Pct.
    """
    if df.empty:
        return pd.DataFrame()

    prices = df[column].dropna()
    shares_bought = initial_amount / prices.iloc[0]

    result = pd.DataFrame(index=prices.index)
    result["Price"] = prices
    result["Portfolio_Value"] = shares_bought * prices
    result["Gain_Loss"] = result["Portfolio_Value"] - initial_amount
    result["Return_Pct"] = (result["Portfolio_Value"] / initial_amount - 1) * 100
    return result


def simulate_sip(
    df: pd.DataFrame, monthly_amount: float, column: str = "Close"
) -> pd.DataFrame:
    """
    Simulate a monthly SIP (Systematic Investment Plan).

    Invests *monthly_amount* on the first trading day of each month.

    Returns:
        DataFrame with Total_Shares, Total_Invested, Portfolio_Value,
        Gain_Loss, Return_Pct.
    """
    if df.empty:
        return pd.DataFrame()

    prices = df[column].dropna()
    result = pd.DataFrame(index=prices.index)
    result["Price"] = prices

    total_shares = 0.0
    total_invested = 0.0
    last_month = None

    shares_list: list[float] = []
    invested_list: list[float] = []

    for date, price in prices.items():
        current_month = (date.year, date.month)
        if last_month is None or current_month != last_month:
            total_shares += monthly_amount / price
            total_invested += monthly_amount
            last_month = current_month

        shares_list.append(total_shares)
        invested_list.append(total_invested)

    result["Total_Shares"] = shares_list
    result["Total_Invested"] = invested_list
    result["Portfolio_Value"] = result["Total_Shares"] * result["Price"]
    result["Gain_Loss"] = result["Portfolio_Value"] - result["Total_Invested"]
    result["Return_Pct"] = (
        (result["Portfolio_Value"] / result["Total_Invested"] - 1) * 100
    )
    return result
