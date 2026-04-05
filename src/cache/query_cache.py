from __future__ import annotations

import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


DB_PATH = Path("graph.db")


def _init_db() -> None:
    """Initialize the cache table if it doesn't exist."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_cache (
                query_hash TEXT PRIMARY KEY,
                task TEXT,
                answer TEXT,
                created_at TEXT,
                hits INTEGER DEFAULT 0
            )
        """)
        conn.commit()


def _hash_task(task: str) -> str:
    """Generate SHA-256 hash of task string."""
    return hashlib.sha256(task.encode()).hexdigest()


def get_cached(task: str) -> Optional[dict]:
    """
    Get cached agent response for a task.
    Returns the cached result dict, or None if not found.
    Increments hit counter on cache hit.
    """
    _init_db()
    task_hash = _hash_task(task)

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT answer FROM query_cache
            WHERE query_hash = ?
        """, (task_hash,))

        row = cursor.fetchone()
        if not row:
            return None

        # Increment hits counter
        cursor.execute("""
            UPDATE query_cache
            SET hits = hits + 1
            WHERE query_hash = ?
        """, (task_hash,))
        conn.commit()

        # Parse and return answer
        try:
            answer = row[0]
            return {
                "task": task,
                "answer": answer,
                "cached": True,
            }
        except Exception:
            return None


def store_cache(task: str, result: dict) -> None:
    """
    Store agent response in cache.
    result should have keys: task, answer, context_used
    """
    _init_db()
    task_hash = _hash_task(task)
    answer = result.get("answer", "")
    created_at = datetime.now().isoformat()

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO query_cache
                (query_hash, task, answer, created_at, hits)
                VALUES (?, ?, ?, ?, 0)
            """, (task_hash, task, answer, created_at))
            conn.commit()
        except Exception:
            pass


def clear_cache() -> None:
    """Delete all cache entries."""
    _init_db()
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM query_cache")
        conn.commit()


def get_cache_stats() -> dict:
    """Get cache statistics."""
    _init_db()
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM query_cache")
        total_entries = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(hits) FROM query_cache")
        total_hits = cursor.fetchone()[0] or 0

    return {
        "total_entries": total_entries,
        "total_hits": total_hits,
    }

