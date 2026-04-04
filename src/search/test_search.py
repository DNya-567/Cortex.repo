from __future__ import annotations

import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from searcher import search


TEST_QUERIES = [
    "where is user login handled",
    "how is a token generated",
    "database query for finding a user",
]


def main() -> None:
    for query in TEST_QUERIES:
        print(f"Query: {query}")
        results = search(query, top_k=3)

        if not results:
            print("  No results")
        else:
            for item in results:
                print(
                    f"  - {item['chunk_name']} | {item['file_path']} | "
                    f"score={item['score']:.4f}"
                )

        print("-" * 60)


if __name__ == "__main__":
    main()

