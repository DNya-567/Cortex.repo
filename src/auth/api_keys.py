from __future__ import annotations

import sqlite3
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional


DB_PATH = Path("graph.db")


def _init_db() -> None:
    """Initialize API keys table."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key_hash TEXT PRIMARY KEY,
                key_prefix TEXT,
                name TEXT,
                created_at TEXT,
                last_used TEXT,
                is_active INTEGER DEFAULT 1,
                request_count INTEGER DEFAULT 0
            )
        """)
        conn.commit()


def generate_api_key(name: str) -> dict:
    """
    Generate a new API key and store its hash.
    Returns the raw key (shown once), never stored in plaintext.
    """
    _init_db()

    raw_key = "ce-" + secrets.token_hex(16)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:8]
    created_at = datetime.now().isoformat()

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO api_keys 
            (key_hash, key_prefix, name, created_at, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (key_hash, key_prefix, name, created_at))
        conn.commit()

    return {
        "key": raw_key,
        "prefix": key_prefix,
        "name": name,
        "created_at": created_at,
    }


def verify_api_key(key: str) -> bool:
    """
    Verify if an API key is valid and active.
    Updates last_used and request_count.
    """
    _init_db()
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    now = datetime.now().isoformat()

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT is_active FROM api_keys
            WHERE key_hash = ? AND is_active = 1
        """, (key_hash,))

        result = cursor.fetchone()
        if not result:
            return False

        cursor.execute("""
            UPDATE api_keys
            SET last_used = ?, request_count = request_count + 1
            WHERE key_hash = ?
        """, (now, key_hash))
        conn.commit()
        return True


def revoke_api_key(key_prefix: str) -> bool:
    """
    Revoke an API key by its prefix (e.g., 'ce-a3f9b2').
    Returns True if key was found and revoked.
    """
    _init_db()

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE api_keys
            SET is_active = 0
            WHERE key_prefix = ?
        """, (key_prefix,))
        conn.commit()

        if cursor.rowcount > 0:
            return True
        return False


def list_api_keys() -> list[dict]:
    """
    List all API keys (without exposing raw keys).
    Returns metadata about each key.
    """
    _init_db()

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT key_prefix, name, created_at, last_used, is_active, request_count
            FROM api_keys
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()

    return [
        {
            "prefix": row[0],
            "name": row[1],
            "created_at": row[2],
            "last_used": row[3],
            "is_active": row[4],
            "request_count": row[5],
        }
        for row in rows
    ]

