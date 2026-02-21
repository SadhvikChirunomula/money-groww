"""
Plotly chart builders for every visualisation in the dashboard.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from src.config import COLORS, MOVING_AVG_COLORS, CURRENCY_SYMBOL


def _base_layout(title: str = "") -> dict:
    """Shared dark-theme layout settings."""
    return dict(
        title=dict(text=title, font=dict(size=18, color=COLORS["text"])),
        template="plotly_dark",
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=50, r=30, t=50, b=60),
        xaxis=dict(rangeslider=dict(visible=False), gridcolor="#2A2A3E"),
        yaxis=dict(gridcolor="#2A2A3E"),
    )


C = CURRENCY_SYMBOL  # shorthand


# ── Price Chart ───────────────────────────────────────────────────────
def plot_price_chart(
    df: pd.DataFrame,
    ticker: str,
    chart_type: str = "Candlestick",
    ma_columns: list[str] | None = None,
    show_volume: bool = True,
) -> go.Figure:
    rows = 2 if show_volume else 1
    row_heights = [0.75, 0.25] if show_volume else [1]
    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True,
        vertical_spacing=0.04, row_heights=row_heights,
    )

    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"], name="Price",
            increasing_line_color=COLORS["green"],
            decreasing_line_color=COLORS["red"],
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"], mode="lines",
            name="Close", line=dict(color=COLORS["primary"], width=2),
        ), row=1, col=1)

    if ma_columns:
        for i, col in enumerate(ma_columns):
            if col in df.columns:
                color = MOVING_AVG_COLORS[i % len(MOVING_AVG_COLORS)]
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[col], mode="lines",
                    name=col, line=dict(color=color, width=1.5, dash="dot"),
                ), row=1, col=1)

    if show_volume and "Volume" in df.columns:
        colors = [
            COLORS["green"] if c >= o else COLORS["red"]
            for c, o in zip(df["Close"], df["Open"])
        ]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"], name="Volume",
            marker_color=colors, opacity=0.5,
        ), row=2, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)

    fig.update_layout(**_base_layout(f"{ticker} — Price Chart"), height=560)
    fig.update_yaxes(title_text=f"Price ({C})", row=1, col=1)
    return fig


# ── Investment Growth ─────────────────────────────────────────────────
def plot_investment_growth(
    sim_df: pd.DataFrame, ticker: str, initial: float
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sim_df.index, y=sim_df["Portfolio_Value"],
        mode="lines", name="Portfolio Value",
        line=dict(color=COLORS["primary"], width=2.5),
        fill="tozeroy", fillcolor="rgba(108,99,255,0.12)",
    ))
    fig.add_hline(
        y=initial, line_dash="dash", line_color=COLORS["orange"],
        annotation_text=f"Invested: {C}{initial:,.0f}",
        annotation_position="top left",
    )
    fig.update_layout(
        **_base_layout(f"{ticker} — Investment Growth"),
        height=440, yaxis_title=f"Value ({C})",
    )
    return fig


# ── SIP Growth ────────────────────────────────────────────────────────
def plot_sip_growth(sip_df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sip_df.index, y=sip_df["Portfolio_Value"],
        mode="lines", name="Portfolio Value",
        line=dict(color=COLORS["green"], width=2.5),
        fill="tonexty", fillcolor="rgba(0,200,83,0.08)",
    ))
    fig.add_trace(go.Scatter(
        x=sip_df.index, y=sip_df["Total_Invested"],
        mode="lines", name="Total Invested",
        line=dict(color=COLORS["orange"], width=2, dash="dash"),
    ))
    fig.update_layout(
        **_base_layout(f"{ticker} — SIP Growth"),
        height=440, yaxis_title=f"Value ({C})",
    )
    return fig


# ── Portfolio Comparison ──────────────────────────────────────────────
def plot_portfolio_comparison(returns_dict: dict[str, pd.Series]) -> go.Figure:
    fig = go.Figure()
    palette = [
        COLORS["primary"], COLORS["secondary"], COLORS["green"],
        COLORS["cyan"], COLORS["orange"], "#E040FB",
    ]
    for i, (ticker, series) in enumerate(returns_dict.items()):
        fig.add_trace(go.Scatter(
            x=series.index, y=series, mode="lines", name=ticker,
            line=dict(color=palette[i % len(palette)], width=2.5),
        ))
    fig.add_hline(y=0, line_dash="dot", line_color=COLORS["gray"], opacity=0.5)
    fig.update_layout(
        **_base_layout("Portfolio Comparison — Cumulative Returns"),
        height=500, yaxis_title="Return (%)",
    )
    return fig


# ── Returns Distribution ─────────────────────────────────────────────
def plot_returns_distribution(
    daily_returns: pd.Series, ticker: str
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=daily_returns.dropna(), nbinsx=80,
        name="Daily Returns",
        marker_color=COLORS["primary"], opacity=0.75,
    ))
    fig.update_layout(
        **_base_layout(f"{ticker} — Daily Returns Distribution"),
        height=360, xaxis_title="Daily Return (%)", yaxis_title="Frequency",
    )
    return fig


# ── Prediction ────────────────────────────────────────────────────────
def plot_prediction(
    df: pd.DataFrame, prediction_result: dict, ticker: str
) -> go.Figure:
    fig = go.Figure()
    recent = df.tail(60)

    fig.add_trace(go.Scatter(
        x=recent.index, y=recent["Close"],
        mode="lines", name="Actual Price",
        line=dict(color=COLORS["primary"], width=2.5),
    ))

    if prediction_result.get("predictions"):
        pred_dates = [df.index[-1]]
        pred_prices = [df["Close"].iloc[-1]]
        for p in prediction_result["predictions"]:
            pred_dates.append(p["date"])
            pred_prices.append(p["predicted_price"])

        fig.add_trace(go.Scatter(
            x=pred_dates, y=pred_prices,
            mode="lines+markers", name="Predicted",
            line=dict(color=COLORS["orange"], width=3, dash="dash"),
            marker=dict(size=12, symbol="star", color=COLORS["orange"],
                        line=dict(width=2, color=COLORS["text"])),
        ))

        upper = [p * 1.02 for p in pred_prices]
        lower = [p * 0.98 for p in pred_prices]
        fig.add_trace(go.Scatter(
            x=pred_dates, y=upper, mode="lines",
            line=dict(width=0), showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=pred_dates, y=lower, mode="lines",
            fill="tonexty", fillcolor="rgba(255,145,0,0.12)",
            line=dict(width=0), name="Confidence Band",
        ))

        for p in prediction_result["predictions"]:
            fig.add_annotation(
                x=p["date"], y=p["predicted_price"],
                text=f"{C}{p['predicted_price']:,.2f}",
                showarrow=True, arrowhead=2, arrowcolor=COLORS["orange"],
                font=dict(size=13, color=COLORS["orange"]),
                bgcolor="rgba(30,30,46,0.9)", bordercolor=COLORS["orange"],
            )

    fig.update_layout(
        **_base_layout(f"{ticker} — Price Prediction"),
        height=480, yaxis_title=f"Price ({C})",
    )
    return fig


# ── MA Crossover Signals ─────────────────────────────────────────────
def plot_ma_signals(signals_df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=signals_df.index, y=signals_df["Close"],
        mode="lines", name="Price",
        line=dict(color=COLORS["gray"], width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=signals_df.index, y=signals_df["SMA_short"],
        mode="lines", name="SMA Short",
        line=dict(color=COLORS["green"], width=2),
    ))
    fig.add_trace(go.Scatter(
        x=signals_df.index, y=signals_df["SMA_long"],
        mode="lines", name="SMA Long",
        line=dict(color=COLORS["red"], width=2),
    ))

    buys = signals_df[signals_df["signal"] == 1]
    fig.add_trace(go.Scatter(
        x=buys.index, y=buys["Close"],
        mode="markers", name="BUY (Golden Cross)",
        marker=dict(symbol="triangle-up", size=16,
                    color=COLORS["green"], line=dict(width=2, color="white")),
    ))
    sells = signals_df[signals_df["signal"] == -1]
    fig.add_trace(go.Scatter(
        x=sells.index, y=sells["Close"],
        mode="markers", name="SELL (Death Cross)",
        marker=dict(symbol="triangle-down", size=16,
                    color=COLORS["red"], line=dict(width=2, color="white")),
    ))

    fig.update_layout(
        **_base_layout(f"{ticker} — Moving Average Crossover Signals"),
        height=480, yaxis_title=f"Price ({C})",
    )
    return fig


# ── RSI ───────────────────────────────────────────────────────────────
def plot_rsi(rsi_signals_df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rsi_signals_df.index, y=rsi_signals_df["RSI"],
        mode="lines", name="RSI (14)",
        line=dict(color=COLORS["primary"], width=2),
    ))
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS["red"],
                  annotation_text="Overbought (70)")
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["green"],
                  annotation_text="Oversold (30)")
    fig.add_hrect(y0=70, y1=100, fillcolor=COLORS["red"], opacity=0.07)
    fig.add_hrect(y0=0, y1=30, fillcolor=COLORS["green"], opacity=0.07)
    layout = _base_layout(f"{ticker} — RSI")
    layout["yaxis"] = dict(range=[0, 100], gridcolor="#2A2A3E")
    fig.update_layout(**layout, height=300, yaxis_title="RSI")
    return fig


# ── MACD ──────────────────────────────────────────────────────────────
def plot_macd(macd_signals_df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=macd_signals_df.index, y=macd_signals_df["MACD"],
        mode="lines", name="MACD",
        line=dict(color=COLORS["cyan"], width=2),
    ))
    fig.add_trace(go.Scatter(
        x=macd_signals_df.index, y=macd_signals_df["MACD_Signal"],
        mode="lines", name="Signal Line",
        line=dict(color=COLORS["secondary"], width=2),
    ))
    colors = [
        COLORS["green"] if v >= 0 else COLORS["red"]
        for v in macd_signals_df["MACD_Hist"]
    ]
    fig.add_trace(go.Bar(
        x=macd_signals_df.index, y=macd_signals_df["MACD_Hist"],
        name="Histogram", marker_color=colors, opacity=0.6,
    ))

    buys = macd_signals_df[macd_signals_df["signal"] == 1]
    sells = macd_signals_df[macd_signals_df["signal"] == -1]
    fig.add_trace(go.Scatter(
        x=buys.index, y=buys["MACD"], mode="markers", name="BUY",
        marker=dict(symbol="triangle-up", size=12, color=COLORS["green"]),
    ))
    fig.add_trace(go.Scatter(
        x=sells.index, y=sells["MACD"], mode="markers", name="SELL",
        marker=dict(symbol="triangle-down", size=12, color=COLORS["red"]),
    ))
    fig.update_layout(
        **_base_layout(f"{ticker} — MACD"), height=340, yaxis_title="MACD",
    )
    return fig


# ── Recommendation Gauge ─────────────────────────────────────────────
def plot_recommendation_gauge(score: int, verdict: str) -> go.Figure:
    gauge_val = score + 100
    if score >= 60:
        bar_color = COLORS["green"]
    elif score >= 25:
        bar_color = "#66BB6A"
    elif score > -25:
        bar_color = COLORS["orange"]
    elif score > -60:
        bar_color = "#EF5350"
    else:
        bar_color = COLORS["red"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=gauge_val,
        number=dict(suffix="", font=dict(size=36, color=COLORS["text"])),
        title=dict(text=f"Verdict: {verdict}",
                   font=dict(size=20, color=bar_color)),
        gauge=dict(
            axis=dict(
                range=[0, 200],
                tickvals=[0, 50, 100, 150, 200],
                ticktext=["Strong\nSell", "Sell", "Hold", "Buy", "Strong\nBuy"],
                tickfont=dict(size=11),
            ),
            bar=dict(color=bar_color, thickness=0.3),
            bgcolor="#1E1E2E", borderwidth=0,
            steps=[
                dict(range=[0, 40], color="rgba(255,23,68,0.15)"),
                dict(range=[40, 75], color="rgba(239,83,80,0.10)"),
                dict(range=[75, 125], color="rgba(255,145,0,0.10)"),
                dict(range=[125, 160], color="rgba(102,187,106,0.10)"),
                dict(range=[160, 200], color="rgba(0,200,83,0.15)"),
            ],
            threshold=dict(
                line=dict(color="white", width=3),
                thickness=0.8, value=gauge_val,
            ),
        ),
    ))
    fig.update_layout(
        paper_bgcolor=COLORS["bg"], plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        height=280, margin=dict(l=30, r=30, t=60, b=20),
    )
    return fig
