from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from git import Repo


DB_PATH = Path("graph.db")


def _init_db() -> None:
    """Initialize the SQLite database if it doesn't exist."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS git_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                commit_hash TEXT NOT NULL,
                author TEXT,
                date TEXT,
                message TEXT,
                UNIQUE(file_path, commit_hash)
            )
        """)
        conn.commit()


def _get_repo(repo_path: str) -> Repo:
    """Initialize and return a GitPython Repo object."""
    return Repo(repo_path)


def _normalize_file_path(file_path: str) -> str:
    """Normalize file path for consistency (forward slashes)."""
    return file_path.replace("\\", "/")


def get_file_history(repo_path: str, file_path: str, limit: int = 3) -> list[dict]:
    """
    Get the last N commits that touched a given file.
    Returns list of dicts with: commit_hash, author_name, date, message
    """
    _init_db()

    file_path = _normalize_file_path(file_path)

    # Check cache first
    cached_commits = _get_cached_history(file_path)
    if cached_commits:
        return cached_commits[:limit]

    try:
        repo = _get_repo(repo_path)

        # Find commits for this file
        commits = list(repo.iter_commits(paths=file_path, max_count=limit))

        results = []
        for commit in commits:
            commit_info = {
                "commit_hash": commit.hexsha[:7],
                "author_name": commit.author.name,
                "date": datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d"),
                "message": commit.message.split("\n")[0],  # First line only
            }
            results.append(commit_info)

            # Cache the commit
            cache_history(file_path, [commit_info])

        return results

    except Exception:
        # If git fails, return empty list
        return []


def _get_cached_history(file_path: str) -> list[dict]:
    """
    Retrieve cached commit history for a file.
    """
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT commit_hash, author, date, message
            FROM git_cache
            WHERE file_path = ?
            ORDER BY date DESC
        """, (file_path,))

        rows = cursor.fetchall()
        return [
            {
                "commit_hash": row[0],
                "author_name": row[1],
                "date": row[2],
                "message": row[3],
            }
            for row in rows
        ]


def cache_history(file_path: str, commits: list[dict]) -> None:
    """
    Cache commit history for a file in the database.
    """
    _init_db()

    file_path = _normalize_file_path(file_path)

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()

        for commit in commits:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO git_cache
                    (file_path, commit_hash, author, date, message)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    file_path,
                    commit.get("commit_hash", ""),
                    commit.get("author_name", ""),
                    commit.get("date", ""),
                    commit.get("message", ""),
                ))
            except sqlite3.IntegrityError:
                pass

        conn.commit()

