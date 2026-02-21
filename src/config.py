"""
Shared configuration: color palette, ticker lists, period options.
"""

# ── Plotly color palette (dark theme) ─────────────────────────────────
COLORS = {
    "primary": "#6C63FF",
    "secondary": "#FF6584",
    "green": "#00C853",
    "red": "#FF1744",
    "orange": "#FF9100",
    "cyan": "#00E5FF",
    "gray": "#B0BEC5",
    "bg": "#0E1117",
    "card": "#1E1E2E",
    "text": "#FAFAFA",
}

MOVING_AVG_COLORS = [
    "#FFD600", "#FF6D00", "#00E676", "#2979FF", "#E040FB", "#00BCD4",
]

# ── Popular Indian stock tickers — NSE (Groww-style) ─────────────────
POPULAR_TICKERS = {
    "Nifty 50 Large Cap": [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
        "ICICIBANK.NS", "BHARTIARTL.NS", "ITC.NS",
    ],
    "IT & Tech": [
        "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS",
        "TECHM.NS", "LTI.NS",
    ],
    "Banking & Finance": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS",
        "AXISBANK.NS", "BAJFINANCE.NS",
    ],
    "Auto": [
        "TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS",
        "HEROMOTOCO.NS", "EICHERMOT.NS",
    ],
    "Pharma & Health": [
        "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS",
        "APOLLOHOSP.NS",
    ],
    "Energy & Metals": [
        "RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS",
        "TATASTEEL.NS", "HINDALCO.NS",
    ],
    "FMCG": [
        "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS",
        "DABUR.NS", "MARICO.NS",
    ],
    "Indices": ["^NSEI", "^BSESN", "^NSEBANK"],
}

# ── Time-range options (sidebar) ─────────────────────────────────────
PERIOD_OPTIONS = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "2 Years": "2y",
    "5 Years": "5y",
    "10 Years": "10y",
    "Max": "max",
}

DEFAULT_PERIOD_INDEX = 3   # "1 Year"

# ── Currency ──────────────────────────────────────────────────────────
CURRENCY_SYMBOL = "₹"
