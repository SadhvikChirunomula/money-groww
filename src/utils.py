"""
Utility helpers used across the application.
"""


def ensure_ns_suffix(ticker: str) -> str:
    """
    Auto-append .NS (NSE) suffix for plain ticker names so users can type
    just ``RELIANCE`` instead of ``RELIANCE.NS``.

    Leaves tickers that already have a suffix (e.g. ``.NS``, ``.BO``) or
    index symbols (starting with ``^``) unchanged.
    """
    t = ticker.strip().upper()
    if not t:
        return t
    if "." in t or t.startswith("^"):
        return t
    return t + ".NS"
