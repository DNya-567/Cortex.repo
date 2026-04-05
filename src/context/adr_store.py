from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Optional


DB_PATH = Path("graph.db")


def _init_db() -> None:
    """Initialize the SQLite database if it doesn't exist."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adrs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adr_id TEXT UNIQUE,
                title TEXT,
                status TEXT,
                context TEXT,
                decision TEXT,
                consequences TEXT,
                affected_files TEXT
            )
        """)
        conn.commit()


def _parse_adr_file(file_path: Path) -> Optional[dict]:
    """
    Parse a markdown ADR file and extract its structure.
    Expected format:
    # ADR-001: Title here
    ## Status
    accepted
    ## Context
    ...
    ## Decision
    ...
    ## Consequences
    ...
    ## Affected Files
    - file1.js
    - file2.js
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return None

    # Extract ADR ID and title from header
    header_match = re.search(r"#\s+(ADR-\d+):\s*(.+?)$", content, re.MULTILINE)
    if not header_match:
        return None

    adr_id = header_match.group(1)
    title = header_match.group(2).strip()

    # Extract sections
    def extract_section(section_name: str) -> str:
        """Extract content from a ## Section Name section."""
        pattern = rf"##\s+{re.escape(section_name)}\s*\n(.*?)(?=##|$)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    status = extract_section("Status")
    context = extract_section("Context")
    decision = extract_section("Decision")
    consequences = extract_section("Consequences")
    affected_files_section = extract_section("Affected Files")

    # Parse affected files from the list
    affected_files = []
    for line in affected_files_section.split("\n"):
        line = line.strip()
        if line.startswith("-"):
            file_path_str = line[1:].strip()
            if file_path_str:
                affected_files.append(file_path_str)

    return {
        "adr_id": adr_id,
        "title": title,
        "status": status,
        "context": context,
        "decision": decision,
        "consequences": consequences,
        "affected_files": ",".join(affected_files),  # Store as comma-separated string
    }


def load_adrs(adr_directory: str) -> None:
    """
    Load all ADR markdown files from a directory and store them in the database.
    """
    _init_db()

    adr_dir = Path(adr_directory)
    if not adr_dir.exists():
        return

    # Clear existing ADRs for re-loading
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM adrs")
        conn.commit()

    # Find all markdown files
    md_files = adr_dir.glob("*.md")

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()

        for md_file in md_files:
            adr = _parse_adr_file(md_file)
            if adr:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO adrs
                        (adr_id, title, status, context, decision, consequences, affected_files)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        adr["adr_id"],
                        adr["title"],
                        adr["status"],
                        adr["context"],
                        adr["decision"],
                        adr["consequences"],
                        adr["affected_files"],
                    ))
                except sqlite3.IntegrityError:
                    pass

        conn.commit()


def get_adrs_for_file(file_path: str) -> list[dict]:
    """
    Get all ADRs that mention the given file in their affected_files section.
    """
    _init_db()

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT adr_id, title, status, context, decision, consequences, affected_files
            FROM adrs
            WHERE affected_files LIKE ?
        """, (f"%{file_path}%",))

        rows = cursor.fetchall()
        return [
            {
                "adr_id": row[0],
                "title": row[1],
                "status": row[2],
                "context": row[3],
                "decision": row[4],
                "consequences": row[5],
                "affected_files": row[6].split(",") if row[6] else [],
            }
            for row in rows
        ]


def get_all_adrs() -> list[dict]:
    """
    Get all ADRs from the database.
    """
    _init_db()

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT adr_id, title, status, context, decision, consequences, affected_files
            FROM adrs
            ORDER BY adr_id
        """)

        rows = cursor.fetchall()
        return [
            {
                "adr_id": row[0],
                "title": row[1],
                "status": row[2],
                "context": row[3],
                "decision": row[4],
                "consequences": row[5],
                "affected_files": row[6].split(",") if row[6] else [],
            }
            for row in rows
        ]

