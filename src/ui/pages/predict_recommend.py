"""Page 2 — Predict & Recommend (ML predictions + technical signals)."""

import streamlit as st
import pandas as pd

from src.config import CURRENCY_SYMBOL as C
from src.utils import ensure_ns_suffix
from src.data.fetcher import fetch_stock_data, get_stock_info
from src.analysis.predictor import predict_prices
from src.analysis.signals import (
    generate_ma_signals, generate_rsi_signals,
    generate_macd_signals, generate_recommendation,
)
from src.ui.charts import (
    plot_prediction, plot_ma_signals, plot_rsi,
    plot_macd, plot_recommendation_gauge,
)


def render(quick_pick: str) -> None:
    st.subheader("🔮 Predict & Recommend")
    st.caption(
        "ML-powered price predictions + technical signal analysis "
        "to help decide if it's worth investing."
    )

    col_t, col_p = st.columns([2, 3])
    with col_t:
        ticker = ensure_ns_suffix(
            st.text_input("Enter stock ticker", value=quick_pick,
                          placeholder="e.g. RELIANCE, TCS", key="pred_ticker")
        )

    if not ticker:
        st.info("Enter a ticker symbol to get started.")
        st.stop()

    # Fetch enough data — need ≥200 days for SMA-200 + ML features
    with st.spinner(f"Fetching data & running ML models for **{ticker}**…"):
        df = fetch_stock_data(ticker, period="2y")
        info = get_stock_info(ticker)

    if df.empty or len(df) < 100:
        st.error(
            f"Not enough data for **{ticker}** (need ≥100 trading days). "
            "Try a longer period or different ticker."
        )
        st.stop()

    with col_p:
        st.markdown(f"**{info['name']}** — {info['sector']} · {info['industry']}")

    # ── Run prediction ────────────────────────────────────────────
    with st.spinner("Running prediction models…"):
        pred_result = predict_prices(df, days_ahead=2)

    if "error" in pred_result:
        st.error(pred_result["error"])
        st.stop()

    # ── Predicted prices ──────────────────────────────────────────
    st.divider()
    current_price = pred_result["current_price"]
    predictions = pred_result["predictions"]

    cols = st.columns(2 + len(predictions))
    cols[0].metric("Current Price", f"{C}{current_price:,.2f}")
    for i, p in enumerate(predictions):
        day_label = p["date"].strftime("%a %d %b")
        change = p["predicted_price"] - current_price
        cols[i + 1].metric(
            f"Predicted — {day_label}",
            f"{C}{p['predicted_price']:,.2f}",
            delta=f"{C}{change:+.2f} ({(change / current_price) * 100:+.2f}%)",
        )
    cols[-1].metric("Model Confidence", f"{pred_result['confidence']:.0f}%")

    # ── Prediction chart ──────────────────────────────────────────
    fig_pred = plot_prediction(df, pred_result, ticker)
    st.plotly_chart(fig_pred, use_container_width=True)

    # ── Model breakdown ───────────────────────────────────────────
    with st.expander("🤖 Model Details", expanded=False):
        acc = pred_result["model_accuracy"]
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Ridge Regression", f"{acc.get('Ridge', 0):.1f}% R²")
        mc2.metric("Random Forest", f"{acc.get('RandomForest', 0):.1f}% R²")
        mc3.metric("Gradient Boosting", f"{acc.get('GradientBoosting', 0):.1f}% R²")

        if predictions:
            st.markdown("**Per-model predictions:**")
            for p in predictions:
                day_lbl = p["date"].strftime("%a %d %b %Y")
                parts = [
                    f"`{name}`: {C}{val:,.2f}"
                    for name, val in p["model_predictions"].items()
                ]
                st.markdown(f"- **{day_lbl}** → " + " · ".join(parts))

    # ── Technical Signals ─────────────────────────────────────────
    st.divider()
    st.subheader("📡 Technical Signals — Should You Invest?")
    st.caption(
        "Green = bullish (buy), Red = bearish (sell), Yellow = neutral. "
        "The green & red lines show moving average crossovers."
    )

    ma_signals = generate_ma_signals(df, short_window=20, long_window=50)
    rsi_signals = generate_rsi_signals(df)
    macd_signals = generate_macd_signals(df)
    recommendation = generate_recommendation(df, pred_result)

    # ── Recommendation verdict ────────────────────────────────────
    g_col, r_col = st.columns([1, 2])
    with g_col:
        fig_gauge = plot_recommendation_gauge(
            recommendation["score"], recommendation["verdict"]
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with r_col:
        verdict = recommendation["verdict"]
        verdict_colors = {
            "STRONG BUY": "#00C853", "BUY": "#66BB6A", "HOLD": "#FF9100",
            "SELL": "#EF5350", "STRONG SELL": "#FF1744",
        }
        v_color = verdict_colors.get(verdict, "#B0BEC5")

        st.markdown(f"""
        <div style="background:#1E1E2E; border-left:5px solid {v_color};
                    border-radius:8px; padding:20px; margin:10px 0;">
            <h2 style="color:{v_color}; margin:0;">
                {'✅' if 'BUY' in verdict else ('⚠️' if verdict == 'HOLD' else '🚫')} {verdict}
            </h2>
            <p style="color:#FAFAFA; font-size:1.1rem; margin-top:8px;">
                {recommendation['summary']}
            </p>
            <p style="color:#B0BEC5; font-size:0.9rem; margin-top:4px;">
                🟢 {recommendation.get('bullish', 0)} Bullish &nbsp;·&nbsp;
                🔴 {recommendation.get('bearish', 0)} Bearish &nbsp;·&nbsp;
                🟡 {recommendation.get('neutral', 0)} Neutral
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ── Individual signals table ──────────────────────────────────
    if recommendation["signals"]:
        st.markdown("#### Signal Breakdown")
        sig_data = [
            {
                "Signal": s["emoji"],
                "Indicator": s["indicator"],
                "Value": s["value"],
                "Reading": s["signal"],
            }
            for s in recommendation["signals"]
        ]
        st.dataframe(
            pd.DataFrame(sig_data), use_container_width=True, hide_index=True
        )

    # ── Signal charts ─────────────────────────────────────────────
    st.divider()
    tab1, tab2, tab3 = st.tabs(
        ["📈 MA Crossover (Green/Red Lines)", "📊 RSI", "📉 MACD"]
    )

    with tab1:
        st.caption(
            "**Green line** = Short-term SMA (20) · "
            "**Red line** = Long-term SMA (50). "
            "When green crosses above red → BUY (▲). "
            "When green crosses below red → SELL (▼)."
        )
        fig_ma = plot_ma_signals(ma_signals, ticker)
        st.plotly_chart(fig_ma, use_container_width=True)

    with tab2:
        st.caption(
            "RSI below 30 = oversold (potential buy) · "
            "RSI above 70 = overbought (potential sell)."
        )
        fig_rsi = plot_rsi(rsi_signals, ticker)
        st.plotly_chart(fig_rsi, use_container_width=True)

    with tab3:
        st.caption(
            "MACD crossing above signal line → bullish. "
            "MACD crossing below → bearish."
        )
        fig_macd = plot_macd(macd_signals, ticker)
        st.plotly_chart(fig_macd, use_container_width=True)

    # ── Disclaimer ────────────────────────────────────────────────
    st.divider()
    st.warning(
        "⚠️ **Disclaimer:** Predictions are based on historical patterns using "
        "machine learning models. Stock markets are inherently unpredictable. "
        "This is NOT financial advice. Always do your own research and consult "
        "a financial advisor before investing."
    )
