from __future__ import annotations

from src.chunker.chunker import chunk_directory_any


def get_chunk_stats(directory: str) -> dict:
    """Analyze directory and return chunking statistics."""
    chunks = chunk_directory_any(directory)

    by_language = {}
    by_type = {}
    total_lines = 0

    for chunk in chunks:
        lang = chunk.language
        by_language[lang] = by_language.get(lang, 0) + 1

        ctype = chunk.chunk_type
        by_type[ctype] = by_type.get(ctype, 0) + 1

        total_lines += (chunk.end_line - chunk.start_line + 1)

    avg_size = total_lines / len(chunks) if chunks else 0

    return {
        "total_chunks": len(chunks),
        "by_language": by_language,
        "by_type": by_type,
        "files_processed": len(set(c.file_path for c in chunks)),
        "avg_chunk_size_lines": round(avg_size, 2),
    }

