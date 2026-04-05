from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


DB_PATH = Path("graph.db")
WINDOW_SECONDS = 60
LIMIT_PER_WINDOW = 60


def _init_db() -> None:
    """Initialize rate limit table."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                key_prefix TEXT,
                window_start TEXT,
                request_count INTEGER DEFAULT 0,
                PRIMARY KEY (key_prefix, window_start)
            )
        """)
        conn.commit()


def check_rate_limit(key_prefix: str) -> bool:
    """
    Check if request is within rate limit for this key.
    Returns True if under limit, False if exceeded.
    """
    _init_db()

    now = datetime.now()
    window_start = (now - timedelta(
        seconds=now.second % WINDOW_SECONDS,
        microseconds=now.microsecond   # ← was microsecond (wrong)
    )).isoformat()

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT request_count FROM rate_limits
            WHERE key_prefix = ? AND window_start = ?
        """, (key_prefix, window_start))

        result = cursor.fetchone()
        if result:
            count = result[0]
            if count >= LIMIT_PER_WINDOW:
                return False
            cursor.execute("""
                UPDATE rate_limits
                SET request_count = request_count + 1
                WHERE key_prefix = ? AND window_start = ?
            """, (key_prefix, window_start))
        else:
            cursor.execute("""
                INSERT INTO rate_limits (key_prefix, window_start, request_count)
                VALUES (?, ?, 1)
            """, (key_prefix, window_start))

        conn.commit()

    return True


def get_rate_limit_status(key_prefix: str) -> dict:
    """
    Get current rate limit status for a key.
    """
    _init_db()

    now = datetime.now()
    window_start = (now - timedelta(
        seconds=now.second % WINDOW_SECONDS,
        microseconds=now.microsecond   # ← was microsecond (wrong)
    )).isoformat()
    window_end = (datetime.fromisoformat(window_start) + timedelta(seconds=WINDOW_SECONDS)).isoformat()
    reset_in = int((datetime.fromisoformat(window_end) - now).total_seconds())

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT request_count FROM rate_limits
            WHERE key_prefix = ? AND window_start = ?
        """, (key_prefix, window_start))

        result = cursor.fetchone()
        count = result[0] if result else 0

    return {
        "key_prefix": key_prefix,
        "requests_this_window": count,
        "limit": LIMIT_PER_WINDOW,
        "window_seconds": WINDOW_SECONDS,
        "remaining": max(0, LIMIT_PER_WINDOW - count),
        "reset_in_seconds": max(0, reset_in),
    }