from __future__ import annotations

from pathlib import Path

from src.chunker.chunker import CodeChunk


def chunk_generic_file(
    file_path: str, window: int = 50, overlap: int = 10
) -> list[CodeChunk]:
    """
    Generic chunker using sliding window of lines.
    Works for any text-based language.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return []

    if len(lines) < 5:
        return []

    ext = Path(file_path).suffix.lower()
    language = _get_language_from_ext(ext)

    chunks = []
    step = window - overlap
    i = 0
    chunk_num = 1

    while i < len(lines):
        end_idx = min(i + window, len(lines))
        start_line = i + 1
        end_line = end_idx

        content = "".join(lines[i:end_idx]).strip()
        if not content:
            i += step
            continue

        chunk_id = f"{file_path}::block_{chunk_num}::{start_line}"
        chunk = CodeChunk(
            chunk_id=chunk_id,
            file_path=file_path,
            chunk_type="block",
            chunk_name=f"block_{chunk_num}",
            content=content,
            start_line=start_line,
            end_line=end_line,
            language=language,
        )
        chunks.append(chunk)

        i += step
        chunk_num += 1

    return chunks


def _get_language_from_ext(ext: str) -> str:
    """Map file extension to language name."""
    ext_map = {
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".kt": "kotlin",
        ".swift": "swift",
    }
    return ext_map.get(ext.lower(), "unknown")

