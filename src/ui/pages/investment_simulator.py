"""Page 3 — Investment Growth Simulator (lump sum & SIP)."""

import streamlit as st

from src.config import CURRENCY_SYMBOL as C
from src.utils import ensure_ns_suffix
from src.data.fetcher import fetch_stock_data
from src.analysis.simulator import simulate_investment, simulate_sip
from src.ui.charts import plot_investment_growth, plot_sip_growth


def render(quick_pick: str, selected_period: str) -> None:
    st.subheader("💰 Investment Growth Simulator")
    st.caption("See how a lump-sum or SIP investment would have grown over time.")

    col1, col2, col3 = st.columns(3)
    with col1:
        ticker = ensure_ns_suffix(st.text_input("Ticker", value=quick_pick))
    with col2:
        invest_mode = st.radio("Mode", ["Lump Sum", "Monthly SIP"], horizontal=True)
    with col3:
        if invest_mode == "Lump Sum":
            amount = st.number_input(
                f"Investment Amount ({C})",
                min_value=1000, value=100000, step=5000,
            )
        else:
            amount = st.number_input(
                f"Monthly SIP Amount ({C})",
                min_value=500, value=5000, step=500,
            )

    if not ticker:
        st.info("Enter a ticker symbol.")
        st.stop()

    with st.spinner(f"Simulating investment in **{ticker}**…"):
        df = fetch_stock_data(ticker, period=selected_period)

    if df.empty:
        st.error(f"No data for **{ticker}**.")
        st.stop()

    if invest_mode == "Lump Sum":
        sim = simulate_investment(df, amount)
        if not sim.empty:
            r1, r2, r3, r4 = st.columns(4)
            final_val = sim["Portfolio_Value"].iloc[-1]
            gain = sim["Gain_Loss"].iloc[-1]
            ret = sim["Return_Pct"].iloc[-1]
            r1.metric("Invested", f"{C}{amount:,.0f}")
            r2.metric("Current Value", f"{C}{final_val:,.0f}")
            r3.metric("Gain / Loss", f"{C}{gain:+,.0f}")
            r4.metric("Return", f"{ret:+.2f}%")

            fig = plot_investment_growth(sim, ticker, amount)
            st.plotly_chart(fig, use_container_width=True)
    else:
        sim = simulate_sip(df, amount)
        if not sim.empty:
            r1, r2, r3, r4 = st.columns(4)
            total_inv = sim["Total_Invested"].iloc[-1]
            final_val = sim["Portfolio_Value"].iloc[-1]
            gain = sim["Gain_Loss"].iloc[-1]
            ret = sim["Return_Pct"].iloc[-1]
            r1.metric("Total Invested", f"{C}{total_inv:,.0f}")
            r2.metric("Current Value", f"{C}{final_val:,.0f}")
            r3.metric("Gain / Loss", f"{C}{gain:+,.0f}")
            r4.metric("Return", f"{ret:+.2f}%")

            fig = plot_sip_growth(sim, ticker)
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Simulation Data"):
        st.dataframe(
            sim.tail(60).sort_index(ascending=False),
            use_container_width=True,
        )
