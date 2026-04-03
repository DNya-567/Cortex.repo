from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient

from indexer import index_directory


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "code_chunks")


def main() -> None:
    summary = index_directory("test-codebase")
    print(summary)

    client = QdrantClient(url=QDRANT_URL)
    count_result = client.count(collection_name=COLLECTION_NAME, exact=True)
    print(f"Qdrant records: {count_result.count}")

    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=3,
        with_payload=True,
        with_vectors=False,
    )

    print("First 3 stored chunks:")
    for point in points:
        payload = point.payload or {}
        print(f"- {payload.get('chunk_name')} | {payload.get('file_path')}")


if __name__ == "__main__":
    main()

