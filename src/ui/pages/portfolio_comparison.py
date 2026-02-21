"""Page 4 — Portfolio Comparison (multi-stock cumulative returns)."""

import streamlit as st
import pandas as pd

from src.utils import ensure_ns_suffix
from src.data.fetcher import fetch_stock_data
from src.analysis.indicators import compute_cumulative_returns, compute_stats
from src.ui.charts import plot_portfolio_comparison


def render(selected_period: str) -> None:
    st.subheader("📁 Portfolio Comparison")
    st.caption("Compare cumulative returns of multiple stocks side by side.")

    tickers_input = st.text_input(
        "Enter tickers (comma-separated)",
        value="RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS",
        help="e.g. RELIANCE, TCS, SBIN, TATAMOTORS (auto-adds .NS)",
    )
    tickers = [ensure_ns_suffix(t) for t in tickers_input.split(",") if t.strip()]

    if len(tickers) < 2:
        st.warning("Enter at least 2 tickers to compare.")
        st.stop()

    returns_dict: dict[str, pd.Series] = {}
    stats_list: list[dict] = []

    with st.spinner("Fetching data for comparison…"):
        for t in tickers:
            df = fetch_stock_data(t, period=selected_period)
            if not df.empty:
                cum_ret = compute_cumulative_returns(df)
                returns_dict[t] = cum_ret
                s = compute_stats(df)
                s["Ticker"] = t
                stats_list.append(s)

    if len(returns_dict) < 2:
        st.error("Could not fetch data for enough tickers.")
        st.stop()

    # ── Comparison chart ──────────────────────────────────────────
    fig_comp = plot_portfolio_comparison(returns_dict)
    st.plotly_chart(fig_comp, use_container_width=True)

    # ── Comparison table ──────────────────────────────────────────
    if stats_list:
        comp_df = pd.DataFrame(stats_list).set_index("Ticker")
        cols_order = [
            "Current Price", "Total Return (%)", "CAGR (%)",
            "Annualized Volatility (%)", "Max Drawdown (%)",
            "52-Wk High", "52-Wk Low",
        ]
        comp_df = comp_df[[c for c in cols_order if c in comp_df.columns]]
        st.dataframe(comp_df, use_container_width=True)

        best = comp_df["Total Return (%)"].idxmax()
        worst = comp_df["Total Return (%)"].idxmin()
        st.success(
            f"🏆 **Best performer:** {best} "
            f"({comp_df.loc[best, 'Total Return (%)']:+.2f}%)"
        )
        st.error(
            f"📉 **Weakest:** {worst} "
            f"({comp_df.loc[worst, 'Total Return (%)']:+.2f}%)"
        )
