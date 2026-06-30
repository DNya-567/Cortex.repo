from __future__ import annotations
from pathlib import Path
from src.chunker.chunker import chunk_directory, chunk_file
from src.embedder.embedder import get_embedding
from src.storage.qdrant_store import store_chunks_batch, get_collection_name, setup_collection
from src.storage.manifest import load_manifest, save_manifest, hash_content

BATCH_SIZE = 16

# Shared progress state — polled by /index/progress endpoint
indexing_progress = {
    "active": False,
    "total_chunks": 0,
    "processed_chunks": 0,
    "current_file": "",
}


def index_directory(directory: str) -> dict:
    collection_name = get_collection_name(directory)
    setup_collection(collection_name)

    target = Path(directory)
    all_chunks = chunk_directory(target)

    # Group chunks by file so we can hash each file's combined content
    chunks_by_file: dict[str, list] = {}
    for chunk in all_chunks:
        chunks_by_file.setdefault(chunk.file_path, []).append(chunk)

    manifest = load_manifest(collection_name)
    new_manifest: dict[str, str] = {}
    chunks_to_embed = []

    for file_path, file_chunks in chunks_by_file.items():
        combined_content = "".join(c.content for c in file_chunks)
        current_hash = hash_content(combined_content)
        new_manifest[file_path] = current_hash

        if manifest.get(file_path) != current_hash:
            # New or changed file — needs (re-)embedding
            chunks_to_embed.extend(file_chunks)

    total_files = len(chunks_by_file)
    skipped_files = total_files - len({c.file_path for c in chunks_to_embed})

    indexing_progress["active"] = True
    indexing_progress["total_chunks"] = len(chunks_to_embed)
    indexing_progress["processed_chunks"] = 0
    indexing_progress["current_file"] = ""

    try:
        batch_chunks = []
        batch_embeddings = []
        for chunk in chunks_to_embed:
            embedding = get_embedding(chunk.content)
            batch_chunks.append(chunk)
            batch_embeddings.append(embedding)

            indexing_progress["processed_chunks"] += 1
            indexing_progress["current_file"] = chunk.file_path

            if len(batch_chunks) >= BATCH_SIZE:
                store_chunks_batch(batch_chunks, batch_embeddings, collection_name)
                for stored_chunk in batch_chunks:
                    print(f"Stored: {stored_chunk.file_path} | {stored_chunk.chunk_name}")
                batch_chunks = []
                batch_embeddings = []
        if batch_chunks:
            store_chunks_batch(batch_chunks, batch_embeddings, collection_name)
            for stored_chunk in batch_chunks:
                print(f"Stored: {stored_chunk.file_path} | {stored_chunk.chunk_name}")
    finally:
        indexing_progress["active"] = False

    save_manifest(collection_name, new_manifest)

    print(f"[Indexer] {total_files} files total, {skipped_files} unchanged (skipped), {len(chunks_to_embed)} chunks embedded")

    return {
        "total_files": total_files,
        "total_chunks": len(chunks_to_embed),
        "skipped_files": skipped_files,
        "status": "ok",
    }