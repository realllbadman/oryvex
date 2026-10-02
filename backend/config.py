"""Shared environment parsing.

Kept out of main.py so routes and services can import it without a circular
import back through the FastAPI app.
"""
import os


def env_num(key: str, default: str) -> float:
    """Read a numeric env var, tolerating what systemd's EnvironmentFile leaves behind.

    python-dotenv strips a trailing `# comment` from a value; systemd does NOT —
    it only honours `#` at the start of a line. So a server .env written as

        MIN_ORDER=0            # no minimum

    reaches the process as the literal string "0            # no minimum", and a
    bare float() raises ValueError at import time, taking the whole app down
    (nginx then serves 502). Strip the comment, quotes and whitespace before
    converting, and fall back to the default rather than crashing on junk.
    """
    raw = os.getenv(key)
    if raw is None:
        raw = default
    raw = raw.split("#", 1)[0].strip().strip("\"'")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return float(default)


def env_str(key: str, default: str = "") -> str:
    """Same comment/quote tolerance, for plain string settings."""
    raw = os.getenv(key)
    if raw is None:
        raw = default
    return raw.split("#", 1)[0].strip().strip("\"'")


def env_list(key: str, default: str) -> list[str]:
    """Comma-separated setting (e.g. PAYMENT_METHODS), comment-tolerant."""
    return [p.strip() for p in env_str(key, default).split(",") if p.strip()]


# ─── Bundle & save tiers ──────────────────────────────────────────
# Buy more vials of the same size, pay less per vial. `min_qty` is inclusive and
# tiers are matched highest-first, so 7 vials lands on the 5+ tier.
BUNDLE_TIERS = [
    {"key": "x1",  "min_qty": 1,  "pct": 0,  "label": "1 vial",    "sub": "List price", "badge": None,           "pips": 1},
    {"key": "x3",  "min_qty": 3,  "pct": 30, "label": "3+ vials",  "sub": "30% off",    "badge": "Most popular", "pips": 3},
    {"key": "x5",  "min_qty": 5,  "pct": 35, "label": "5+ vials",  "sub": "35% off",    "badge": "Best value",   "pips": 3},
    {"key": "x10", "min_qty": 10, "pct": 40, "label": "10+ vials", "sub": "40% off",    "badge": "Bulk",         "pips": 3},
]


def bundle_pct(qty: int) -> int:
    """Discount percentage earned by buying `qty` of one line item."""
    pct = 0
    for tier in BUNDLE_TIERS:
        if qty >= tier["min_qty"]:
            pct = tier["pct"]
    return pct


def bundle_unit_price(list_price: float, qty: int) -> float:
    """Per-unit price after the bundle discount for that quantity."""
    return round(list_price * (100 - bundle_pct(qty)) / 100.0, 2)
