from __future__ import annotations

import os
from pathlib import Path
import uuid

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from chunker.chunker import CodeChunk


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "code_chunks")
VECTOR_SIZE = 768

_client = QdrantClient(url=QDRANT_URL)


def setup_collection() -> None:
    existing_collections = _client.get_collections().collections
    names = {collection.name for collection in existing_collections}

    if COLLECTION_NAME not in names:
        _client.create_collection(
            collection_name=COLLECTION_NAME,
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


def store_chunk(chunk: CodeChunk, embedding: list[float]) -> None:
    setup_collection()

    if len(embedding) != VECTOR_SIZE:
        raise ValueError(f"Expected embedding size {VECTOR_SIZE}, got {len(embedding)}")

    point = PointStruct(
        id=_point_id(chunk.chunk_id),
        vector=embedding,
        payload=_chunk_payload(chunk),
    )

    _client.upsert(collection_name=COLLECTION_NAME, points=[point], wait=True)


def store_chunks_batch(chunks: list[CodeChunk], embeddings: list[list[float]]) -> None:
    setup_collection()

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
        _client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
