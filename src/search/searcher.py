from __future__ import annotations

from qdrant_client import QdrantClient

from src.embedder.embedder import get_embedding
from src.storage.qdrant_store import QDRANT_URL, setup_collection, get_collection_name


_client = QdrantClient(url=QDRANT_URL)


def _search_points(query_vector: list[float], limit: int, collection_name: str):
    from src.storage.qdrant_store import _with_retry

    def do_query():
        response = _client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return response.points

    return _with_retry(do_query)


def search(query: str, top_k: int = 5, repo_path: str = ".") -> list[dict]:
    cleaned_query = query.strip()
    if not cleaned_query:
        return []

    limit = max(1, top_k)
    collection_name = get_collection_name(repo_path)
    setup_collection(collection_name)

    query_vector = get_embedding(cleaned_query)
    points = _search_points(query_vector=query_vector, limit=limit, collection_name=collection_name)

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