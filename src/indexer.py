from __future__ import annotations

from pathlib import Path

from src.chunker.chunker import chunk_directory
from src.embedder.embedder import get_embedding
from src.storage.qdrant_store import store_chunks_batch


BATCH_SIZE = 16


def index_directory(directory: str) -> dict:
    target = Path(directory)
    chunks = chunk_directory(target)
    total_files = len({chunk.file_path for chunk in chunks})

    batch_chunks = []
    batch_embeddings = []

    for chunk in chunks:
        embedding = get_embedding(chunk.content)
        batch_chunks.append(chunk)
        batch_embeddings.append(embedding)

        if len(batch_chunks) >= BATCH_SIZE:
            store_chunks_batch(batch_chunks, batch_embeddings)
            for stored_chunk in batch_chunks:
                print(f"Stored: {stored_chunk.file_path} | {stored_chunk.chunk_name}")
            batch_chunks = []
            batch_embeddings = []

    if batch_chunks:
        store_chunks_batch(batch_chunks, batch_embeddings)
        for stored_chunk in batch_chunks:
            print(f"Stored: {stored_chunk.file_path} | {stored_chunk.chunk_name}")

    return {
        "total_files": total_files,
        "total_chunks": len(chunks),
        "status": "ok",
    }

