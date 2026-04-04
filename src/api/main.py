from __future__ import annotations

from fastapi import FastAPI, Query

from src.search.searcher import search


app = FastAPI(title="Context Engine Search API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/search")
def search_endpoint(query: str = Query(..., min_length=1), top_k: int = Query(5, ge=1, le=50)) -> dict:
    results = search(query=query, top_k=top_k)
    return {
        "query": query,
        "total": len(results),
        "results": results,
    }

