"""
Technical signals and investment recommendation engine.

Generates buy / sell signals from MA crossovers, RSI, MACD and produces
an overall "worth investing" verdict.
"""

import pandas as pd
import numpy as np


# ══════════════════════════════════════════════════════════════════════
#  Indicator helpers
# ══════════════════════════════════════════════════════════════════════

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_macd(
    series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
):
    """MACD line, signal line, and histogram."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


# ══════════════════════════════════════════════════════════════════════
#  Signal generators
# ══════════════════════════════════════════════════════════════════════

def generate_ma_signals(
    df: pd.DataFrame, short_window: int = 20, long_window: int = 50
) -> pd.DataFrame:
    """
    Golden Cross (short > long) → BUY.
    Death Cross  (short < long) → SELL.
    """
    signals = pd.DataFrame(index=df.index)
    signals["Close"] = df["Close"]
    signals["SMA_short"] = df["Close"].rolling(short_window).mean()
    signals["SMA_long"] = df["Close"].rolling(long_window).mean()

    signals["position"] = 0
    signals.loc[signals["SMA_short"] > signals["SMA_long"], "position"] = 1
    signals["signal"] = signals["position"].diff()
    return signals


def generate_rsi_signals(
    df: pd.DataFrame, period: int = 14,
    overbought: float = 70, oversold: float = 30,
) -> pd.DataFrame:
    """RSI-based buy / sell signals."""
    signals = pd.DataFrame(index=df.index)
    signals["Close"] = df["Close"]
    signals["RSI"] = compute_rsi(df["Close"], period)

    signals["signal"] = 0
    signals.loc[signals["RSI"] < oversold, "signal"] = 1
    signals.loc[signals["RSI"] > overbought, "signal"] = -1
    return signals


def generate_macd_signals(df: pd.DataFrame) -> pd.DataFrame:
    """MACD crossover signals."""
    signals = pd.DataFrame(index=df.index)
    signals["Close"] = df["Close"]
    macd_line, signal_line, histogram = compute_macd(df["Close"])
    signals["MACD"] = macd_line
    signals["MACD_Signal"] = signal_line
    signals["MACD_Hist"] = histogram

    signals["position"] = 0
    signals.loc[signals["MACD"] > signals["MACD_Signal"], "position"] = 1
    signals["signal"] = signals["position"].diff()
    return signals


# ══════════════════════════════════════════════════════════════════════
#  Overall recommendation
# ══════════════════════════════════════════════════════════════════════

def _score_indicator(value: float, bull: float, bear: float) -> int:
    if value > bull:
        return 1
    elif value < bear:
        return -1
    return 0


def generate_recommendation(
    df: pd.DataFrame, prediction_result: dict | None = None
) -> dict:
    """
    Combine technical signals + ML prediction into a single verdict:
    STRONG BUY | BUY | HOLD | SELL | STRONG SELL.
    """
    close = df["Close"]
    current_price = close.iloc[-1]
    individual_signals: list[dict] = []

    # 1. MA Crossover 20/50
    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]
    if not (np.isnan(sma20) or np.isnan(sma50)):
        ma_bullish = sma20 > sma50
        individual_signals.append({
            "indicator": "MA Crossover (20/50)",
            "value": f"SMA20={sma20:.2f}, SMA50={sma50:.2f}",
            "signal": "Bullish" if ma_bullish else "Bearish",
            "score": 1 if ma_bullish else -1,
            "emoji": "🟢" if ma_bullish else "🔴",
        })

    # 2. Price vs SMA 200
    sma200 = close.rolling(200).mean().iloc[-1]
    if not np.isnan(sma200):
        above = current_price > sma200
        individual_signals.append({
            "indicator": "Price vs SMA 200",
            "value": f"Price={current_price:.2f}, SMA200={sma200:.2f}",
            "signal": "Bullish" if above else "Bearish",
            "score": 1 if above else -1,
            "emoji": "🟢" if above else "🔴",
        })

    # 3. RSI
    rsi = compute_rsi(close).iloc[-1]
    if not np.isnan(rsi):
        if rsi < 30:
            rsi_sig, rsi_sc = "Oversold (Buy)", 1
        elif rsi > 70:
            rsi_sig, rsi_sc = "Overbought (Sell)", -1
        else:
            rsi_sig, rsi_sc = "Neutral", 0
        individual_signals.append({
            "indicator": "RSI (14)",
            "value": f"{rsi:.1f}",
            "signal": rsi_sig,
            "score": rsi_sc,
            "emoji": "🟢" if rsi_sc > 0 else ("🔴" if rsi_sc < 0 else "🟡"),
        })

    # 4. MACD
    macd_line, signal_line, _ = compute_macd(close)
    macd_val, sig_val = macd_line.iloc[-1], signal_line.iloc[-1]
    if not (np.isnan(macd_val) or np.isnan(sig_val)):
        macd_bull = macd_val > sig_val
        individual_signals.append({
            "indicator": "MACD",
            "value": f"MACD={macd_val:.2f}, Signal={sig_val:.2f}",
            "signal": "Bullish" if macd_bull else "Bearish",
            "score": 1 if macd_bull else -1,
            "emoji": "🟢" if macd_bull else "🔴",
        })

    # 5. 5-Day momentum
    if len(close) >= 6:
        ret_5d = (close.iloc[-1] / close.iloc[-6] - 1) * 100
        mom = _score_indicator(ret_5d, 1.0, -1.0)
        individual_signals.append({
            "indicator": "5-Day Momentum",
            "value": f"{ret_5d:+.2f}%",
            "signal": "Bullish" if mom > 0 else ("Bearish" if mom < 0 else "Neutral"),
            "score": mom,
            "emoji": "🟢" if mom > 0 else ("🔴" if mom < 0 else "🟡"),
        })

    # 6. Volatility
    if len(close) >= 21:
        vol = close.pct_change().tail(20).std() * np.sqrt(252) * 100
        vs = 0 if vol < 30 else -1
        individual_signals.append({
            "indicator": "Volatility (20d ann.)",
            "value": f"{vol:.1f}%",
            "signal": "Low Risk" if vol < 20 else ("Moderate" if vol < 30 else "High Risk"),
            "score": vs,
            "emoji": "🟢" if vol < 20 else ("🟡" if vol < 30 else "🔴"),
        })

    # 7. ML Prediction
    if prediction_result and prediction_result.get("predictions"):
        pred_change = prediction_result.get("predicted_change_pct", 0)
        pred_trend = prediction_result.get("trend", "neutral")
        confidence = prediction_result.get("confidence", 0)
        ps = 1 if pred_trend == "bullish" else (-1 if pred_trend == "bearish" else 0)
        individual_signals.append({
            "indicator": f"ML Prediction ({confidence:.0f}% conf.)",
            "value": f"{pred_change:+.2f}% predicted",
            "signal": pred_trend.capitalize(),
            "score": ps,
            "emoji": "🟢" if ps > 0 else ("🔴" if ps < 0 else "🟡"),
        })

    if not individual_signals:
        return {
            "verdict": "INSUFFICIENT DATA", "score": 0,
            "signals": [], "summary": "Not enough data.",
        }

    total = sum(s["score"] for s in individual_signals)
    norm = round((total / len(individual_signals)) * 100)

    if norm >= 60:
        verdict = "STRONG BUY"
    elif norm >= 25:
        verdict = "BUY"
    elif norm > -25:
        verdict = "HOLD"
    elif norm > -60:
        verdict = "SELL"
    else:
        verdict = "STRONG SELL"

    bull = sum(1 for s in individual_signals if s["score"] > 0)
    bear = sum(1 for s in individual_signals if s["score"] < 0)
    neut = sum(1 for s in individual_signals if s["score"] == 0)

    parts = [f"{bull} bullish, {bear} bearish, {neut} neutral signal(s)."]
    if verdict in ("STRONG BUY", "BUY"):
        parts.append("Technical indicators suggest this could be a good time to invest.")
    elif verdict == "HOLD":
        parts.append("Mixed signals — consider waiting for a clearer trend.")
    else:
        parts.append("Indicators are mostly bearish — wait or reduce exposure.")

    return {
        "verdict": verdict, "score": norm,
        "signals": individual_signals, "summary": " ".join(parts),
        "bullish": bull, "bearish": bear, "neutral": neut,
    }
