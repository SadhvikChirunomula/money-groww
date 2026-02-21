# 📈 Money Grow — Indian Stock Market Analysis Dashboard

A **Streamlit** web-app for analysing Indian (NSE) stock-market patterns,
running **ML-powered price predictions**, generating buy/sell signals, and
simulating investment growth — all in **₹ (INR)**.

---

## ✨ Features

| Page                        | What it does                                                                                                                             |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **📊 Stock Analysis**       | Candlestick / line charts, SMA & EMA overlays, volume bars, daily-returns histogram, key statistics (CAGR, volatility, drawdown).        |
| **🔮 Predict & Recommend**  | 1–2 day price forecast using an ML ensemble, plus MA-crossover / RSI / MACD technical signals and a composite BUY / SELL / HOLD verdict. |
| **💰 Investment Simulator** | Lump-sum or monthly SIP back-test showing portfolio growth, gain/loss, and return %.                                                     |
| **📁 Portfolio Comparison** | Side-by-side cumulative-return chart and stats table for multiple tickers.                                                               |

---

## 🗂️ Project Structure

```log
money-grow/
├── app.py                          # Streamlit entry-point (thin router)
├── requirements.txt                # Python dependencies
├── .gitignore
├── README.md
└── src/                            # Application package
    ├── __init__.py
    ├── config.py                   # Colours, tickers, period map, currency
    ├── utils.py                    # Helpers (ensure_ns_suffix, etc.)
    ├── data/
    │   ├── __init__.py
    │   └── fetcher.py              # Yahoo Finance data fetching
    ├── analysis/
    │   ├── __init__.py
    │   ├── indicators.py           # SMA, EMA, returns, stats, volatility
    │   ├── simulator.py            # Lump-sum & SIP simulators
    │   ├── predictor.py            # ML ensemble price predictor
    │   └── signals.py              # MA / RSI / MACD signals & recommendation
    └── ui/
        ├── __init__.py
        ├── charts.py               # All Plotly chart builders
        └── pages/
            ├── __init__.py
            ├── stock_analysis.py        # Page 1
            ├── predict_recommend.py     # Page 2
            ├── investment_simulator.py  # Page 3
            └── portfolio_comparison.py  # Page 4
```

---

## 🚀 Setup

### Prerequisites

- **Python 3.10+**
- **pip** (or any Python package manager)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-user>/money-grow.git
cd money-grow

# 2. Create & activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

### Running the app

```bash
python3 -m streamlit run app.py --server.headless true
```

The dashboard opens at **<http://localhost:8501>**.

---

## 📦 Dependencies

| Package            | Purpose                 |
| ------------------ | ----------------------- |
| `streamlit`        | Web UI framework        |
| `plotly`           | Interactive charts      |
| `yfinance`         | Yahoo Finance data API  |
| `pandas` / `numpy` | Data manipulation       |
| `scikit-learn`     | Machine-learning models |

All listed in [`requirements.txt`](requirements.txt).

---

## 🔮 How the Prediction Works

### Feature Engineering

The predictor (`src/analysis/predictor.py`) builds **40+ features** from raw OHLCV data:

| Category               | Examples                                                              |
| ---------------------- | --------------------------------------------------------------------- |
| Price returns          | 1-day, 2-day, 5-day, 10-day returns                                   |
| Moving averages        | SMA & EMA for 5 / 10 / 20 / 50 / 200 periods, plus price-to-MA ratios |
| Volatility             | 5-, 10-, 20-day rolling standard deviation of returns                 |
| Volume dynamics        | Volume-change %, 5- & 20-day volume SMA                               |
| Momentum / oscillators | RSI-14, MACD, MACD signal, MACD histogram                             |
| Trend features         | Price relative to Bollinger Bands, 52-week high/low ratios            |
| Calendar               | Day-of-week and month encoded as numerics                             |

### Ensemble Model

Three regressors are trained on an 80/20 time-ordered split:

1. **Ridge Regression** — linear baseline with L2 regularisation
2. **Random Forest** (100 trees) — captures non-linear interactions
3. **Gradient Boosting** (200 estimators) — sequential error correction

Their predictions are combined via a **weighted average** (weights proportional
to each model's R² on the validation set) to produce the final forecast for the
next 1–2 trading days.

### Confidence Score

The displayed confidence is the weighted-average R² (clamped to 0–100 %).
A higher score means the models explain more of the historical variance,
though past accuracy does **not** guarantee future results.

---

## 📡 How Buy / Sell Signals Work

The recommendation engine (`src/analysis/signals.py`) evaluates **three
independent technical indicators** and merges them into a single verdict.

### 1. Moving Average Crossover

- Computes a **short-window SMA (20)** and a **long-window SMA (50)**.
- **Golden Cross** (short crosses above long) → BUY signal.
- **Death Cross** (short crosses below long) → SELL signal.

### 2. RSI (Relative Strength Index, 14-period)

- RSI < 30 → **oversold** → potential BUY.
- RSI > 70 → **overbought** → potential SELL.
- 30 ≤ RSI ≤ 70 → neutral.

### 3. MACD (12 / 26 / 9)

- MACD line crosses **above** signal line → BUY.
- MACD line crosses **below** signal line → SELL.

### Composite Score

Each indicator contributes a score (bullish +1, bearish −1, neutral 0).
The ML prediction trend is also factored in.
All scores are summed and mapped to a **−100 … +100 scale**, which drives
the gauge and the final **STRONG BUY / BUY / HOLD / SELL / STRONG SELL**
verdict displayed on the dashboard.

---

## ⚠️ Disclaimer

> This project is for **educational and informational purposes only**.
> It is **NOT financial advice**.
> Stock markets are inherently unpredictable — always do your own research
> and consult a qualified financial advisor before investing.

---

## 📜 Licence

MIT © 2026 **Sadhvik Chirunomula** — feel free to use, modify, and distribute.
