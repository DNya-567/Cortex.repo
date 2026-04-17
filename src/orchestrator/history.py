"""
Orchestration run history storage and retrieval.
Stores runs in SQLite for replay, comparison, and audit.
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path


DB_PATH = Path("graph.db")


def _init_db():
    """Initialize orchestration tables in graph.db."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS orchestration_runs (
            run_id TEXT PRIMARY KEY,
            task TEXT,
            mode TEXT,
            agents_used TEXT,
            final_answer TEXT,
            total_duration_ms INTEGER,
            created_at TEXT,
            subtask_count INTEGER
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS orchestration_subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            subtask_id INTEGER,
            description TEXT,
            agent TEXT,
            answer TEXT,
            duration_ms INTEGER,
            error TEXT,
            FOREIGN KEY (run_id) REFERENCES orchestration_runs(run_id)
        )
    """
    )

    conn.commit()
    conn.close()


def save_run(result: dict) -> str:
    """
    Save full run result to DB.
    Returns run_id.
    """
    _init_db()

    # Generate run_id
    timestamp = datetime.now().isoformat()
    hash_input = (result["task"] + timestamp).encode()
    run_id = hashlib.sha256(hash_input).hexdigest()[:8]

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Save run
    c.execute(
        """
        INSERT INTO orchestration_runs
        (run_id, task, mode, agents_used, final_answer,
         total_duration_ms, created_at, subtask_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            run_id,
            result["task"],
            result.get("mode", "auto"),
            json.dumps(result.get("agents_used", [])),
            result.get("final_answer", ""),
            result.get("total_duration_ms", 0),
            timestamp,
            len(result.get("subtasks", [])),
        ),
    )

    # Save subtasks
    for subtask in result.get("subtasks", []):
        c.execute(
            """
            INSERT INTO orchestration_subtasks
            (run_id, subtask_id, description, agent, answer, duration_ms, error)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                run_id,
                subtask.get("subtask_id"),
                subtask.get("description", ""),
                subtask.get("agent", ""),
                subtask.get("answer", ""),
                subtask.get("duration_ms", 0),
                subtask.get("error"),
            ),
        )

    conn.commit()
    conn.close()

    return run_id


def get_run(run_id: str) -> dict | None:
    """
    Get full run with subtasks.
    Returns dict or None if not found.
    """
    _init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get run
    c.execute("SELECT * FROM orchestration_runs WHERE run_id = ?", (run_id,))
    run_row = c.fetchone()

    if not run_row:
        conn.close()
        return None

    # Get subtasks
    c.execute(
        "SELECT * FROM orchestration_subtasks WHERE run_id = ? ORDER BY subtask_id",
        (run_id,),
    )
    subtask_rows = c.fetchall()
    conn.close()

    # Convert to dict
    result = {
        "run_id": run_row["run_id"],
        "task": run_row["task"],
        "mode": run_row["mode"],
        "agents_used": json.loads(run_row["agents_used"]),
        "final_answer": run_row["final_answer"],
        "total_duration_ms": run_row["total_duration_ms"],
        "created_at": run_row["created_at"],
        "subtasks": [
            {
                "subtask_id": row["subtask_id"],
                "description": row["description"],
                "agent": row["agent"],
                "answer": row["answer"],
                "duration_ms": row["duration_ms"],
                "error": row["error"],
            }
            for row in subtask_rows
        ],
    }

    return result


def list_runs(limit: int = 20) -> list[dict]:
    """
    Get recent runs (summary only, no subtasks).
    Returns list of run summaries.
    """
    _init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute(
        """
        SELECT run_id, task, mode, agents_used, created_at, subtask_count
        FROM orchestration_runs
        ORDER BY created_at DESC
        LIMIT ?
    """,
        (limit,),
    )
    rows = c.fetchall()
    conn.close()

    return [
        {
            "run_id": row["run_id"],
            "task": row["task"],
            "mode": row["mode"],
            "agents_used": json.loads(row["agents_used"]),
            "created_at": row["created_at"],
            "subtask_count": row["subtask_count"],
        }
        for row in rows
    ]


def delete_run(run_id: str) -> bool:
    """
    Delete run and its subtasks.
    Returns True if found and deleted.
    """
    _init_db()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Check if exists
    c.execute("SELECT run_id FROM orchestration_runs WHERE run_id = ?", (run_id,))
    if not c.fetchone():
        conn.close()
        return False

    # Delete subtasks and run
    c.execute("DELETE FROM orchestration_subtasks WHERE run_id = ?", (run_id,))
    c.execute("DELETE FROM orchestration_runs WHERE run_id = ?", (run_id,))

    conn.commit()
    conn.close()
    return True

