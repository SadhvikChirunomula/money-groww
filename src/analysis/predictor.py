"""
ML-based stock price prediction.

Uses an ensemble of Ridge Regression, Random Forest, and Gradient Boosting
trained on 40+ engineered features to predict the next 1–2 trading-day
closing prices.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from datetime import timedelta


# ─────────────────────────────────────────────────────────────────────
#  Feature engineering
# ─────────────────────────────────────────────────────────────────────
def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer 40+ features from OHLCV data."""
    feat = pd.DataFrame(index=df.index)
    close = df["Close"]

    # Lag features
    for lag in [1, 2, 3, 5, 10]:
        feat[f"lag_{lag}"] = close.shift(lag)

    # Rolling stats
    for window in [5, 10, 20, 50]:
        feat[f"sma_{window}"] = close.rolling(window).mean()
        feat[f"std_{window}"] = close.rolling(window).std()
        feat[f"min_{window}"] = close.rolling(window).min()
        feat[f"max_{window}"] = close.rolling(window).max()

    # Price ratios
    feat["close_to_sma5"] = close / feat["sma_5"]
    feat["close_to_sma20"] = close / feat["sma_20"]
    feat["close_to_sma50"] = close / feat["sma_50"]

    # Momentum / returns
    for d in [1, 2, 3, 5, 10, 20]:
        feat[f"return_{d}d"] = close.pct_change(d)

    # Volatility
    feat["volatility_10"] = close.pct_change().rolling(10).std()
    feat["volatility_20"] = close.pct_change().rolling(20).std()

    # RSI (14)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    feat["rsi_14"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    feat["macd"] = ema12 - ema26
    feat["macd_signal"] = feat["macd"].ewm(span=9, adjust=False).mean()
    feat["macd_hist"] = feat["macd"] - feat["macd_signal"]

    # Volume features
    if "Volume" in df.columns:
        vol = df["Volume"].replace(0, np.nan)
        feat["volume_sma5"] = vol.rolling(5).mean()
        feat["volume_ratio"] = vol / feat["volume_sma5"]
        feat["volume_change"] = vol.pct_change()

    # High-Low range
    if "High" in df.columns and "Low" in df.columns:
        feat["hl_range"] = (df["High"] - df["Low"]) / close
        feat["hl_range_sma5"] = feat["hl_range"].rolling(5).mean()

    # Day of week
    feat["day_of_week"] = df.index.dayofweek

    return feat


# ─────────────────────────────────────────────────────────────────────
#  Prediction
# ─────────────────────────────────────────────────────────────────────
def predict_prices(df: pd.DataFrame, days_ahead: int = 2) -> dict:
    """
    Predict the next *days_ahead* closing prices.

    Returns a dict with keys:
        predictions, confidence, model_accuracy, current_price,
        predicted_change_pct, trend, recent_actual
    """
    if len(df) < 100:
        return {"error": "Need at least 100 trading days of data for prediction."}

    features = _build_features(df)
    target = df["Close"]

    combined = features.copy()
    combined["target"] = target
    combined = combined.dropna()

    if len(combined) < 60:
        return {"error": "Not enough clean data after feature engineering."}

    X = combined.drop(columns=["target"])
    y = combined["target"]

    scaler = StandardScaler()
    X_scaled = pd.DataFrame(
        scaler.fit_transform(X), index=X.index, columns=X.columns
    )

    split_idx = int(len(X_scaled) * 0.8)
    X_train, X_val = X_scaled.iloc[:split_idx], X_scaled.iloc[split_idx:]
    y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

    # ── Train ensemble ────────────────────────────────────────────────
    models = {
        "Ridge": Ridge(alpha=1.0),
        "RandomForest": RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
        ),
    }

    model_scores: dict[str, float] = {}
    trained_models: dict = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        score = model.score(X_val, y_val)
        model_scores[name] = round(max(score, 0) * 100, 1)
        trained_models[name] = model

    # Retrain on full data for final prediction
    for name, model in models.items():
        model.fit(X_scaled, y)
        trained_models[name] = model

    # ── Generate predictions ──────────────────────────────────────────
    predictions: list[dict] = []
    last_date = df.index[-1]
    current_df = df.copy()

    for step in range(1, days_ahead + 1):
        feat_row = _build_features(current_df).dropna()
        if feat_row.empty:
            break

        last_feat = feat_row.iloc[[-1]]
        last_feat_scaled = pd.DataFrame(
            scaler.transform(last_feat), columns=last_feat.columns
        )

        preds, weights = {}, {}
        for name, model in trained_models.items():
            p = model.predict(last_feat_scaled)[0]
            w = max(model_scores.get(name, 50), 1)
            preds[name] = p
            weights[name] = w

        total_weight = sum(weights.values())
        ensemble_pred = sum(preds[n] * weights[n] for n in preds) / total_weight

        next_date = last_date + timedelta(days=step)
        while next_date.weekday() >= 5:
            next_date += timedelta(days=1)

        predictions.append(
            {
                "date": next_date,
                "predicted_price": round(ensemble_pred, 2),
                "model_predictions": {n: round(v, 2) for n, v in preds.items()},
            }
        )

        # Append predicted row for iterative forecasting
        new_row = current_df.iloc[-1:].copy()
        new_row.index = [next_date]
        new_row["Close"] = ensemble_pred
        new_row["Open"] = ensemble_pred
        new_row["High"] = ensemble_pred * 1.005
        new_row["Low"] = ensemble_pred * 0.995
        current_df = pd.concat([current_df, new_row])

    # ── Trend detection ───────────────────────────────────────────────
    current_price = df["Close"].iloc[-1]
    if predictions:
        last_pred = predictions[-1]["predicted_price"]
        change_pct = (last_pred - current_price) / current_price * 100
        trend = (
            "bullish" if change_pct > 0.5
            else "bearish" if change_pct < -0.5
            else "neutral"
        )
    else:
        trend, change_pct = "neutral", 0.0

    avg_score = np.mean(list(model_scores.values()))
    confidence = min(round(avg_score, 1), 95)

    return {
        "predictions": predictions,
        "confidence": confidence,
        "model_accuracy": model_scores,
        "current_price": round(current_price, 2),
        "predicted_change_pct": round(change_pct, 2),
        "trend": trend,
        "recent_actual": list(
            zip(
                df.index[-5:].strftime("%Y-%m-%d"),
                df["Close"].tail(5).round(2).tolist(),
            )
        ),
    }
