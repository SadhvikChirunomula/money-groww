"""
Money Grow — Stock Market Analysis Dashboard
=============================================
Thin entry-point that bootstraps Streamlit, sets up the sidebar, and
dispatches to the page renderers in ``src.ui.pages``.
"""

import streamlit as st

from src.config import POPULAR_TICKERS, PERIOD_OPTIONS
from src.ui.pages import stock_analysis, predict_recommend, investment_simulator, portfolio_comparison

# ── Page config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Money Grow — Stock Analyser",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container {padding-top: 1.5rem;}
    .stMetric {background: #1E1E2E; border-radius: 10px; padding: 12px 16px;}
    div[data-testid="stMetricValue"] {font-size: 1.4rem;}
    .big-title {
        font-size: 2.2rem; font-weight: 700;
        background: linear-gradient(90deg, #6C63FF, #FF6584);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {color: #B0BEC5; font-size: 1rem; margin-bottom: 1.5rem;}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────
st.markdown('<div class="big-title">📈 Money Grow</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Analyse Indian stock market patterns &amp; visualise your investment potential</div>', unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔧 Settings")

    page = st.radio(
        "Dashboard",
        ["📊 Stock Analysis", "🔮 Predict & Recommend",
         "💰 Investment Simulator", "📁 Portfolio Comparison"],
        label_visibility="collapsed",
    )

    st.divider()

    st.subheader("Quick Pick")
    category = st.selectbox("Category", list(POPULAR_TICKERS.keys()))
    quick_pick = st.selectbox("Ticker", POPULAR_TICKERS[category])

    st.divider()

    st.subheader("Time Range")
    selected_period_label = st.selectbox("Period", list(PERIOD_OPTIONS.keys()), index=3)
    selected_period = PERIOD_OPTIONS[selected_period_label]

# ── Page router ───────────────────────────────────────────────────────
if page == "📊 Stock Analysis":
    stock_analysis.render(quick_pick, selected_period)
elif page == "🔮 Predict & Recommend":
    predict_recommend.render(quick_pick)
elif page == "💰 Investment Simulator":
    investment_simulator.render(quick_pick, selected_period)
elif page == "📁 Portfolio Comparison":
    portfolio_comparison.render(selected_period)

# ── Footer ────────────────────────────────────────────────────────────
st.divider()
st.caption("Money Grow · Indian Stock Market · Data from Yahoo Finance · Not financial advice · Built with Streamlit & Plotly")
