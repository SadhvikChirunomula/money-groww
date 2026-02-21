"""Page 5 — Browse All Stocks (searchable list with pagination)."""

import streamlit as st
import pandas as pd

from src.config import POPULAR_TICKERS, CURRENCY_SYMBOL as C, COLORS
from src.data.fetcher import fetch_stock_data, get_stock_info, search_tickers
from src.utils import ensure_ns_suffix

# Number of stocks per page
PAGE_SIZE = 12


def _all_tickers() -> list[str]:
    """Flatten POPULAR_TICKERS into a unique ordered list."""
    seen: set[str] = set()
    result: list[str] = []
    for tickers in POPULAR_TICKERS.values():
        for t in tickers:
            if t not in seen and not t.startswith("^"):
                seen.add(t)
                result.append(t)
    return result


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_quick_info(ticker: str) -> dict:
    """Fetch price + basic info for one ticker (cached 10 min)."""
    info = get_stock_info(ticker)
    df = fetch_stock_data(ticker, period="5d")
    price = df["Close"].iloc[-1] if not df.empty else 0
    prev = df["Close"].iloc[-2] if len(df) >= 2 else price
    change = ((price - prev) / prev * 100) if prev else 0
    return {
        "Ticker": ticker.replace(".NS", ""),
        "Symbol": ticker,
        "Company": info.get("name", ticker),
        "Sector": info.get("sector", "—"),
        "Price": price,
        "Change (%)": change,
    }


def render() -> None:
    st.subheader("🏢 Browse All Stocks")
    st.caption(
        "Search for any Indian NSE stock or browse the curated list. "
        "Click a stock to jump to Analysis or Prediction."
    )

    # ── Search ────────────────────────────────────────────────────
    search_query = st.text_input(
        "🔍 Search companies or tickers",
        placeholder="e.g. Tata, Infosys, SBIN…",
        key="browse_search",
    )

    all_stocks = _all_tickers()

    # ── Filter by search or category ──────────────────────────────
    if search_query and len(search_query) >= 2:
        # Use Yahoo Finance search API
        api_results = search_tickers(search_query)
        if api_results:
            filtered = [sym for _, sym in api_results]
        else:
            q = search_query.strip().upper()
            filtered = [t for t in all_stocks if q in t.upper().replace(".NS", "")]
    else:
        # Category filter
        cats = ["All"] + list(POPULAR_TICKERS.keys())
        selected_cat = st.selectbox("Filter by sector", cats, key="browse_cat")
        if selected_cat == "All":
            filtered = all_stocks
        else:
            filtered = [
                t for t in POPULAR_TICKERS[selected_cat]
                if not t.startswith("^")
            ]

    if not filtered:
        st.warning("No stocks match your search. Try a different keyword.")
        return

    # ── Pagination ────────────────────────────────────────────────
    total = len(filtered)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    pag_col1, pag_col2, pag_col3 = st.columns([1, 2, 1])
    with pag_col2:
        current_page = st.number_input(
            f"Page (1–{total_pages})", min_value=1, max_value=total_pages,
            value=1, step=1, key="browse_page",
        )
    st.caption(f"Showing {min(PAGE_SIZE, total - (current_page - 1) * PAGE_SIZE)} of {total} stocks · Page {current_page}/{total_pages}")

    start = (current_page - 1) * PAGE_SIZE
    page_tickers = filtered[start : start + PAGE_SIZE]

    # ── Fetch info for this page ──────────────────────────────────
    with st.spinner("Loading stock data…"):
        rows = []
        for t in page_tickers:
            try:
                rows.append(_fetch_quick_info(t))
            except Exception:
                rows.append({
                    "Ticker": t.replace(".NS", ""),
                    "Symbol": t,
                    "Company": t,
                    "Sector": "—",
                    "Price": 0,
                    "Change (%)": 0,
                })

    # ── Render stock cards ────────────────────────────────────────
    cols_per_row = 3
    for row_start in range(0, len(rows), cols_per_row):
        cols = st.columns(cols_per_row)
        for idx, col in enumerate(cols):
            ri = row_start + idx
            if ri >= len(rows):
                break
            r = rows[ri]
            change_color = COLORS["green"] if r["Change (%)"] >= 0 else COLORS["red"]
            change_arrow = "▲" if r["Change (%)"] >= 0 else "▼"

            with col:
                st.markdown(
                    f"""
                    <div style="background:{COLORS['card']}; border-radius:12px;
                                padding:18px; margin-bottom:12px; border:1px solid #2A2A3E;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span style="font-size:1.1rem; font-weight:700; color:{COLORS['text']};">
                                    {r['Ticker']}
                                </span>
                                <br/>
                                <span style="font-size:0.8rem; color:{COLORS['gray']};">
                                    {r['Company'][:30]}
                                </span>
                            </div>
                            <div style="text-align:right;">
                                <span style="font-size:1.1rem; font-weight:700; color:{COLORS['text']};">
                                    {C}{r['Price']:,.2f}
                                </span>
                                <br/>
                                <span style="font-size:0.85rem; color:{change_color};">
                                    {change_arrow} {r['Change (%)']:+.2f}%
                                </span>
                            </div>
                        </div>
                        <div style="font-size:0.75rem; color:{COLORS['gray']}; margin-top:6px;">
                            {r['Sector']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Navigation buttons
                b1, b2 = st.columns(2)
                with b1:
                    if st.button(
                        "📊 Analyse",
                        key=f"analyse_{r['Symbol']}",
                        use_container_width=True,
                    ):
                        st.session_state["nav_ticker"] = r["Symbol"]
                        st.session_state["nav_page"] = "📊 Stock Analysis"
                        st.rerun()
                with b2:
                    if st.button(
                        "🔮 Predict",
                        key=f"predict_{r['Symbol']}",
                        use_container_width=True,
                    ):
                        st.session_state["nav_ticker"] = r["Symbol"]
                        st.session_state["nav_page"] = "🔮 Predict & Recommend"
                        st.rerun()
