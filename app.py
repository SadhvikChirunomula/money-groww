"""
Money Grow — Stock Market Analysis Dashboard
=============================================
Thin entry-point that bootstraps Streamlit, sets up the sidebar, and
dispatches to the page renderers in ``src.ui.pages``.
"""

import streamlit as st
from streamlit_searchbox import st_searchbox

from src.config import POPULAR_TICKERS, PERIOD_OPTIONS
from src.data.fetcher import search_tickers
from src.utils import ensure_ns_suffix
from src.ui.pages import (
    stock_analysis, predict_recommend, investment_simulator,
    portfolio_comparison, browse_stocks,
)

# ── Page config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Money Grow — Stock Analyser",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Handle navigation from Browse page ────────────────────────────────
# When a user clicks "Analyse" or "Predict" on a stock card, these
# session-state keys are set and we redirect to the target page.
NAV_PAGES = [
    "🏢 Browse Stocks",
    "📊 Stock Analysis",
    "🔮 Predict & Recommend",
    "💰 Investment Simulator",
    "📁 Portfolio Comparison",
]

if "nav_page" in st.session_state:
    _target_page = st.session_state.pop("nav_page")
    default_page_idx = NAV_PAGES.index(_target_page) if _target_page in NAV_PAGES else 0
else:
    default_page_idx = 0

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
        NAV_PAGES,
        index=default_page_idx,
        label_visibility="collapsed",
    )

    st.divider()

    # --- Searchable ticker input ---
    st.subheader("🔍 Search Stock")
    searched = st_searchbox(
        search_tickers,
        placeholder="Type company name or ticker…",
        key="ticker_search",
        clear_on_submit=False,
    )

    st.divider()

    # --- Quick pick fallback ---
    st.subheader("Quick Pick")
    category = st.selectbox("Category", list(POPULAR_TICKERS.keys()))
    quick_pick = st.selectbox("Ticker", POPULAR_TICKERS[category])

    st.divider()

    st.subheader("Time Range")
    selected_period_label = st.selectbox("Period", list(PERIOD_OPTIONS.keys()), index=3)
    selected_period = PERIOD_OPTIONS[selected_period_label]

# Resolve the ticker: nav_ticker > search > quick pick
if "nav_ticker" in st.session_state:
    active_ticker = st.session_state.pop("nav_ticker")
elif searched:
    active_ticker = ensure_ns_suffix(searched)
else:
    active_ticker = quick_pick

# ── Page router ───────────────────────────────────────────────────────
if page == "🏢 Browse Stocks":
    browse_stocks.render()
elif page == "📊 Stock Analysis":
    stock_analysis.render(active_ticker, selected_period)
elif page == "🔮 Predict & Recommend":
    predict_recommend.render(active_ticker)
elif page == "💰 Investment Simulator":
    investment_simulator.render(active_ticker, selected_period)
elif page == "📁 Portfolio Comparison":
    portfolio_comparison.render(selected_period)

# ── Footer ────────────────────────────────────────────────────────────
st.divider()
st.caption("© 2026 Sadhvik Chirunomula · Money Grow · Indian Stock Market · Data from Yahoo Finance · Not financial advice · Built with Streamlit & Plotly")
