from __future__ import annotations

import os
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
            CREATE TABLE IF NOT EXISTS dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                imported_file TEXT NOT NULL,
                imported_names TEXT,
                UNIQUE(source_file, imported_file)
            )
        """)
        conn.commit()


def _normalize_path(path: str) -> str:
    """Normalize path separators to forward slashes."""
    return path.replace("\\", "/")


def _extract_imports_from_file(file_path: Path, root_dir: Path) -> list[dict]:
    """
    Extract all import/require statements from a JavaScript file.
    Returns list of dicts with 'imported_file' and 'imported_names'.
    Paths are stored relative to the PROJECT ROOT (i.e. root_dir's parent),
    so they match the keys callers use — e.g. "test-codebase/auth.js".
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return []

    imports = []

    # ES6: import { x, y } from './module'  or  import x from './module'
    es6_pattern = r"import\s+(.+?)\s+from\s+['\"]([^'\"]+)['\"]"
    for match in re.finditer(es6_pattern, content):
        imported_names = match.group(1).strip()
        imported_path = match.group(2)
        if imported_path.startswith("."):
            imports.append({
                "imported_path": imported_path,
                "imported_names": imported_names,
            })

    # CommonJS: const x = require('./module')
    commonjs_pattern = r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
    for match in re.finditer(commonjs_pattern, content):
        imported_path = match.group(1)
        if imported_path.startswith("."):
            imports.append({
                "imported_path": imported_path,
                "imported_names": "*",
            })

    # Resolve each relative path and store relative to PROJECT ROOT
    # root_dir = test-codebase (absolute), root_dir.parent = project root
    project_root = root_dir.parent
    resolved_imports = []

    for imp in imports:
        resolved_path = _resolve_relative_path(file_path, imp["imported_path"])
        if resolved_path:
            # Store path relative to project root so callers can use
            # "test-codebase/auth.js" style keys consistently
            rel = _normalize_path(str(resolved_path.relative_to(project_root)))
            resolved_imports.append({
                "imported_file": rel,
                "imported_names": imp["imported_names"],
            })

    return resolved_imports


def _resolve_relative_path(source_file: Path, relative_path: str) -> Optional[Path]:
    """
    Resolve a relative import path to an actual file on disk.
    Tries .js, .ts, .jsx, .tsx extensions automatically.
    """
    source_dir = source_file.parent
    relative_path = relative_path.rstrip("/")

    candidate = (source_dir / relative_path).resolve()

    # Directory with index file
    if candidate.is_dir():
        for idx in ["index.js", "index.ts", "index.jsx", "index.tsx"]:
            idx_path = candidate / idx
            if idx_path.exists():
                return idx_path

    # Already has a valid extension
    if candidate.exists() and candidate.is_file():
        return candidate

    # Try adding extensions
    for ext in [".js", ".ts", ".jsx", ".tsx"]:
        with_ext = (source_dir / (relative_path + ext)).resolve()
        if with_ext.exists() and with_ext.is_file():
            return with_ext

    return None


def build_graph(directory: str) -> None:
    """
    Build a dependency graph by scanning all JS/TS files in `directory`.
    Keys stored in DB use project-root-relative paths:
      e.g. "test-codebase/auth.js" -> "test-codebase/userRepository.js"
    This matches the keys used by get_dependencies() / get_dependents().
    """
    _init_db()

    root_dir = Path(directory).resolve()       # absolute path to test-codebase
    project_root = root_dir.parent             # absolute path to project root

    # ------------------------------------------------------------------ #
    # Clear old rows whose source_file starts with the directory prefix   #
    # e.g. "test-codebase/"                                               #
    # ------------------------------------------------------------------ #
    dir_prefix = _normalize_path(directory).rstrip("/") + "/"
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM dependencies WHERE source_file LIKE ?",
            (dir_prefix + "%",),
        )
        conn.commit()

    # Collect all JS/TS files under root_dir
    file_extensions = {".js", ".ts", ".jsx", ".tsx"}
    files_to_process = [
        fp for fp in root_dir.rglob("*")
        if fp.is_file()
           and fp.suffix in file_extensions
           and not any(
            part in fp.parts
            for part in ["node_modules", ".git", "venv", "__pycache__"]
        )
    ]

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()

        for file_path in files_to_process:
            # Source key is relative to PROJECT ROOT → "test-codebase/auth.js"
            source_key = _normalize_path(
                str(file_path.relative_to(project_root))
            )
            imports = _extract_imports_from_file(file_path, root_dir)

            for imp in imports:
                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO dependencies
                            (source_file, imported_file, imported_names)
                        VALUES (?, ?, ?)
                        """,
                        (source_key, imp["imported_file"], imp["imported_names"]),
                    )
                except sqlite3.IntegrityError:
                    pass

        conn.commit()


def get_dependencies(file_path: str) -> list[dict]:
    """
    Get all files that `file_path` imports (upstream dependencies).
    Pass the project-root-relative path, e.g. "test-codebase/auth.js".
    """
    _init_db()
    file_path = _normalize_path(file_path)

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT imported_file, imported_names
            FROM dependencies
            WHERE source_file = ?
            """,
            (file_path,),
        )
        rows = cursor.fetchall()
        return [
            {"imported_file": row[0], "imported_names": row[1]}
            for row in rows
        ]


def get_dependents(file_path: str) -> list[dict]:
    """
    Get all files that import `file_path` (downstream dependents).
    Pass the project-root-relative path, e.g. "test-codebase/utils.js".
    """
    _init_db()
    file_path = _normalize_path(file_path)

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT source_file
            FROM dependencies
            WHERE imported_file = ?
            """,
            (file_path,),
        )
        rows = cursor.fetchall()
        return [{"source_file": row[0]} for row in rows]