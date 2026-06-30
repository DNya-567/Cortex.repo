from __future__ import annotations

import os
from pathlib import Path
import uuid
import hashlib
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
import time
from src.chunker.chunker import CodeChunk


load_dotenv(Path(__file__).resolve().parents[2] / ".env")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
VECTOR_SIZE = 768
_client = QdrantClient(url=QDRANT_URL)


def get_collection_name(directory: str) -> str:
    """
    Deterministic collection name per project directory.
    Same directory always maps to the same collection name.
    """
    normalized = str(Path(directory).resolve()).lower()
    path_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return f"code_chunks_{path_hash}"




def _with_retry(func, max_attempts: int = 3, delay_seconds: float = 1.5):
    """
    Retry a Qdrant call a few times if it times out or briefly fails.
    Qdrant can be momentarily busy right after a large indexing batch.
    """
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as e:
            last_error = e
            if attempt < max_attempts:
                time.sleep(delay_seconds)
    raise last_error

def setup_collection(collection_name: str) -> None:
    existing_collections = _with_retry(lambda: _client.get_collections().collections)
    names = {collection.name for collection in existing_collections}
    if collection_name not in names:
        _with_retry(lambda: _client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        ))

def clear_collection(collection_name: str) -> None:
    """Delete and recreate the collection — wipes all stored chunks."""
    try:
        _client.delete_collection(collection_name=collection_name)
    except Exception:
        pass  # collection may not exist yet
    _client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )


def _chunk_payload(chunk: CodeChunk) -> dict:
    return {
        "chunk_id": chunk.chunk_id,
        "file_path": chunk.file_path,
        "chunk_type": chunk.chunk_type,
        "chunk_name": chunk.chunk_name,
        "content": chunk.content,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "language": chunk.language,
    }


def _point_id(chunk_id: str) -> str:
    # Deterministic UUID keeps upserts stable across re-index runs.
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def store_chunk(chunk: CodeChunk, embedding: list[float], collection_name: str) -> None:
    setup_collection(collection_name)
    if len(embedding) != VECTOR_SIZE:
        raise ValueError(f"Expected embedding size {VECTOR_SIZE}, got {len(embedding)}")
    point = PointStruct(
        id=_point_id(chunk.chunk_id),
        vector=embedding,
        payload=_chunk_payload(chunk),
    )
    _client.upsert(collection_name=collection_name, points=[point], wait=True)


def store_chunks_batch(chunks: list[CodeChunk], embeddings: list[list[float]], collection_name: str) -> None:
    setup_collection(collection_name)
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings must have the same length")
    points: list[PointStruct] = []
    for chunk, embedding in zip(chunks, embeddings):
        if len(embedding) != VECTOR_SIZE:
            raise ValueError(f"Expected embedding size {VECTOR_SIZE}, got {len(embedding)}")
        points.append(
            PointStruct(
                id=_point_id(chunk.chunk_id),
                vector=embedding,
                payload=_chunk_payload(chunk),
            )
        )
    if points:
        _client.upsert(collection_name=collection_name, points=points, wait=True)


def get_collection_size(collection_name: str) -> int:
    """Get the number of points in a collection."""
    try:
        collection_info = _client.get_collection(collection_name)
        return collection_info.points_count
    except Exception:
        return 0
