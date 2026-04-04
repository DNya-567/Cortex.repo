from __future__ import annotations

from qdrant_client import QdrantClient

from src.embedder.embedder import get_embedding
from src.storage.qdrant_store import COLLECTION_NAME, QDRANT_URL, setup_collection


_client = QdrantClient(url=QDRANT_URL)


def _search_points(query_vector: list[float], limit: int):
    response = _client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    return response.points


def search(query: str, top_k: int = 5) -> list[dict]:
    cleaned_query = query.strip()
    if not cleaned_query:
        return []

    limit = max(1, top_k)
    setup_collection()

    query_vector = get_embedding(cleaned_query)
    points = _search_points(query_vector=query_vector, limit=limit)

    results: list[dict] = []
    for point in points:
        payload = point.payload or {}
        score = float(point.score)
        normalized_score = max(0.0, min(1.0, score))

        results.append(
            {
                "chunk_name": payload.get("chunk_name", ""),
                "file_path": payload.get("file_path", ""),
                "chunk_type": payload.get("chunk_type", ""),
                "start_line": int(payload.get("start_line", 0)),
                "end_line": int(payload.get("end_line", 0)),
                "content": payload.get("content", ""),
                "score": normalized_score,
            }
        )

    return results
