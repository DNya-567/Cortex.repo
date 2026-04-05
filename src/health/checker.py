from __future__ import annotations

import sqlite3
from pathlib import Path

import httpx


DB_PATH = Path("graph.db")
OLLAMA_URL = "http://localhost:11434"
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "code_chunks"


def check_health() -> dict:
    """
    Check health of all external dependencies.
    Returns comprehensive health status dict.
    """
    health = {
        "ollama": _check_ollama(),
        "qdrant": _check_qdrant(),
        "qdrant_collection": _check_qdrant_collection(),
        "sqlite": _check_sqlite(),
        "overall": "healthy",
    }

    # Determine overall status
    statuses = [
        health["ollama"]["status"],
        health["qdrant"]["status"],
        health["qdrant_collection"]["status"],
        health["sqlite"]["status"],
    ]

    if all(s == "ok" for s in statuses):
        health["overall"] = "healthy"
    elif any(s == "ok" for s in statuses):
        health["overall"] = "degraded"
    else:
        health["overall"] = "unhealthy"

    return health


def _check_ollama() -> dict:
    """Check if Ollama is reachable."""
    try:
        client = httpx.Client(timeout=5.0)
        response = client.get(OLLAMA_URL)
        client.close()
        if response.status_code == 200:
            return {"status": "ok", "message": f"Ollama reachable at {OLLAMA_URL}"}
        else:
            return {"status": "error", "message": f"Ollama returned {response.status_code}"}
    except httpx.ConnectError as e:
        return {"status": "error", "message": f"Cannot connect to Ollama: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Ollama check failed: {e}"}


def _check_qdrant() -> dict:
    """Check if Qdrant is reachable."""
    try:
        client = httpx.Client(timeout=5.0)
        response = client.get(QDRANT_URL)
        client.close()
        if response.status_code == 200:
            return {"status": "ok", "message": f"Qdrant reachable at {QDRANT_URL}"}
        else:
            return {"status": "error", "message": f"Qdrant returned {response.status_code}"}
    except httpx.ConnectError as e:
        return {"status": "error", "message": f"Cannot connect to Qdrant: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Qdrant check failed: {e}"}


def _check_qdrant_collection() -> dict:
    """Check if Qdrant collection exists."""
    try:
        client = httpx.Client(timeout=5.0)
        response = client.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
        client.close()
        if response.status_code == 200:
            return {"status": "ok", "message": f"Collection '{COLLECTION_NAME}' exists"}
        else:
            return {"status": "error", "message": f"Collection '{COLLECTION_NAME}' not found"}
    except Exception as e:
        return {"status": "error", "message": f"Collection check failed: {e}"}


def _check_sqlite() -> dict:
    """Check if SQLite database is readable."""
    try:
        if not DB_PATH.exists():
            return {"status": "error", "message": f"Database file not found at {DB_PATH}"}

        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            result = cursor.fetchone()

        if result:
            return {"status": "ok", "message": f"SQLite database readable at {DB_PATH}"}
        else:
            return {"status": "error", "message": "SQLite database is empty"}
    except Exception as e:
        return {"status": "error", "message": f"SQLite check failed: {e}"}

