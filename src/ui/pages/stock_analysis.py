"""Page 1 — Stock Analysis (price chart, moving averages, returns)."""

import streamlit as st

from src.config import CURRENCY_SYMBOL as C
from src.data.fetcher import fetch_stock_data, get_stock_info
from src.analysis.indicators import (
    add_sma, add_ema, compute_daily_returns, compute_stats,
)
from src.ui.charts import plot_price_chart, plot_returns_distribution


def render(ticker: str, selected_period: str) -> None:
    if not ticker:
        st.info("Search or pick a stock from the sidebar to get started.")
        st.stop()

    col_info = st.container()

    # Fetch data
    with st.spinner(f"Fetching data for **{ticker}**…"):
        df = fetch_stock_data(ticker, period=selected_period)
        info = get_stock_info(ticker)

    if df.empty:
        st.error(f"No data found for **{ticker}**. Please check the symbol and try again.")
        st.stop()

    # ── Stock info banner ─────────────────────────────────────────
    col_info.markdown(f"**{info['name']}** — {info['sector']} · {info['industry']}")

    stats = compute_stats(df)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Current Price", f"{C}{stats['Current Price']:,.2f}")
    m2.metric("Total Return", f"{stats['Total Return (%)']:+.2f}%")
    m3.metric("CAGR", f"{stats['CAGR (%)']:+.2f}%")
    m4.metric("Volatility", f"{stats['Annualized Volatility (%)']:.2f}%")
    m5.metric("Max Drawdown", f"{stats['Max Drawdown (%)']:.2f}%")

    st.divider()

    # ── Chart controls ────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
    with c1:
        chart_type = st.selectbox("Chart Type", ["Candlestick", "Line"])
    with c2:
        show_volume = st.checkbox("Volume", value=True)
    with c3:
        ma_type = st.selectbox("Moving Average", ["None", "SMA", "EMA", "Both"])
    with c4:
        ma_windows_str = st.text_input("MA Windows", value="20, 50, 200")
        ma_windows = [
            int(x.strip()) for x in ma_windows_str.split(",") if x.strip().isdigit()
        ]

    ma_cols: list[str] = []
    if ma_type in ("SMA", "Both"):
        df = add_sma(df, windows=ma_windows)
        ma_cols += [f"SMA_{w}" for w in ma_windows]
    if ma_type in ("EMA", "Both"):
        df = add_ema(df, windows=ma_windows)
        ma_cols += [f"EMA_{w}" for w in ma_windows]

    # ── Price chart ───────────────────────────────────────────────
    fig_price = plot_price_chart(df, ticker, chart_type,
                                ma_columns=ma_cols, show_volume=show_volume)
    st.plotly_chart(fig_price, use_container_width=True)

    # ── Returns distribution ──────────────────────────────────────
    with st.expander("📉 Daily Returns Distribution", expanded=False):
        daily_ret = compute_daily_returns(df)
        fig_dist = plot_returns_distribution(daily_ret, ticker)
        st.plotly_chart(fig_dist, use_container_width=True)

    # ── Raw data table ────────────────────────────────────────────
    with st.expander("🗂️ Raw Data", expanded=False):
        st.dataframe(df.tail(100).sort_index(ascending=False),
                     use_container_width=True)
