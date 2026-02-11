"""
Two-tier caching layer.

- In-memory dict with TTL for quotes, chains, and computed data.
- SQLite for persistent historical daily prices (append-only).
"""

import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory cache with TTL
# ---------------------------------------------------------------------------

_cache: dict[str, dict[str, Any]] = {}


def get(key: str) -> Any | None:
    """Get a cached value if it exists and is not stale."""
    entry = _cache.get(key)
    if entry is None:
        return None
    if time.time() > entry["expires_at"]:
        del _cache[key]
        return None
    return entry["value"]


def set(key: str, value: Any, ttl_seconds: int = 300) -> None:  # noqa: A001
    """Store a value with a time-to-live (default 5 minutes)."""
    _cache[key] = {
        "value": value,
        "expires_at": time.time() + ttl_seconds,
        "stored_at": datetime.now(),
    }


def is_stale(key: str) -> bool:
    """Return True if the key is missing or expired."""
    return get(key) is None


def get_last_refresh_time() -> datetime | None:
    """Return the most recent stored_at across all cache entries."""
    if not _cache:
        return None
    latest = max(entry["stored_at"] for entry in _cache.values())
    return latest


def clear() -> None:
    """Clear the entire in-memory cache."""
    _cache.clear()


# ---------------------------------------------------------------------------
# SQLite persistent cache for historical daily prices
# ---------------------------------------------------------------------------

_DB_PATH = Path(__file__).parent.parent / "data_cache.db"


def _get_db_connection() -> sqlite3.Connection:
    """Get (or create) a connection to the SQLite cache database."""
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS historical_prices (
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (symbol, date)
        )
    """)
    conn.commit()
    return conn


def save_historical(symbol: str, df: pd.DataFrame) -> None:
    """
    Persist daily OHLCV data to SQLite (upsert).

    Expects DataFrame indexed by Date with Open, High, Low, Close, Volume.
    """
    if df.empty:
        return

    conn = _get_db_connection()
    try:
        for idx, row in df.iterrows():
            date_str = pd.Timestamp(idx).strftime("%Y-%m-%d")
            conn.execute(
                """
                INSERT OR REPLACE INTO historical_prices
                    (symbol, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    date_str,
                    float(row.get("Open", 0)),
                    float(row.get("High", 0)),
                    float(row.get("Low", 0)),
                    float(row.get("Close", 0)),
                    int(row.get("Volume", 0)),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def load_historical(symbol: str, days: int = 150) -> pd.DataFrame:
    """
    Load cached historical data from SQLite.

    Returns DataFrame indexed by Date with Open, High, Low, Close, Volume.
    Returns empty DataFrame if no data is found.
    """
    conn = _get_db_connection()
    try:
        query = """
            SELECT date, open, high, low, close, volume
            FROM historical_prices
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(symbol, days))
        if df.empty:
            return pd.DataFrame()

        df.columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date").sort_index()
        return df
    finally:
        conn.close()
