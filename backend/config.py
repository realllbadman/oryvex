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
