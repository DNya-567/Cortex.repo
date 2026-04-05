from __future__ import annotations

import threading

from fastapi import FastAPI, Query, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse

from src.search.searcher import search
from src.context.context_pack import assemble_context_pack
from src.agent.ollama_agent import query_agent
from src.agent.watcher import start_watcher
from src.health.checker import check_health
from src.cache.query_cache import get_cache_stats, clear_cache
from src.graph.import_resolver import get_dependencies, get_dependents
from src.context.adr_store import get_adrs_for_file
from src.reporter.report import generate_report
from src.auth.middleware import require_auth
from src.auth.api_keys import generate_api_key, list_api_keys, revoke_api_key


app = FastAPI(title="Context Engine Search API")

_watchers = {}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/search")
def search_endpoint(
    query: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=50),
    _auth=Depends(require_auth)
) -> dict:
    results = search(query=query, top_k=top_k)
    return {
        "query": query,
        "total": len(results),
        "results": results,
    }


@app.get("/context-pack")
def context_pack_endpoint(
    task: str = Query(..., min_length=1),
    _auth=Depends(require_auth)
) -> dict:
    """
    Assemble a comprehensive context pack for a given task.
    Returns chunks, dependencies, ADRs, and git history organized from least to most critical.
    """
    if not task or not task.strip():
        raise HTTPException(status_code=400, detail="task parameter is required and cannot be empty")

    try:
        context_pack = assemble_context_pack(task=task, repo_path=".")
        return context_pack
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assemble context pack: {str(e)}"
        )


@app.get("/ask")
def ask_endpoint(
    task: str = Query(..., min_length=1),
    _auth=Depends(require_auth)
) -> dict:
    """
    Query the AI agent with a task. Returns answer based on codebase context.
    """
    if not task or not task.strip():
        raise HTTPException(status_code=400, detail="task parameter is required and cannot be empty")

    try:
        result = query_agent(task=task, repo_path=".")
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent query failed: {str(e)}"
        )


@app.post("/watch")
def watch_endpoint(body: dict) -> dict:
    """
    Start watching a directory for changes and auto-reindex.
    Body: {"directory": "test-codebase"}
    """
    directory = body.get("directory", "test-codebase")

    if directory in _watchers:
        return {"status": "already_watching", "directory": directory}

    try:
        thread = threading.Thread(target=start_watcher, args=(directory,), daemon=True)
        thread.start()
        _watchers[directory] = thread
        return {"status": "watching", "directory": directory}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start watcher: {str(e)}"
        )


@app.get("/health/full")
def health_full_endpoint() -> dict:
    """Check health of all external dependencies."""
    return check_health()


@app.get("/cache/stats")
def cache_stats_endpoint() -> dict:
    """Get cache statistics."""
    return get_cache_stats()


@app.delete("/cache")
def cache_clear_endpoint() -> dict:
    """Clear all cache entries."""
    clear_cache()
    return {"status": "cleared"}


@app.get("/graph/dependencies")
def graph_dependencies_endpoint(file: str = Query(..., min_length=1)) -> dict:
    """Get files that the given file imports."""
    if not file or not file.strip():
        raise HTTPException(status_code=400, detail="file parameter is required")

    try:
        dependencies = get_dependencies(file)
        return {
            "file": file,
            "dependencies": dependencies,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/dependents")
def graph_dependents_endpoint(file: str = Query(..., min_length=1)) -> dict:
    """Get files that import the given file."""
    if not file or not file.strip():
        raise HTTPException(status_code=400, detail="file parameter is required")

    try:
        dependents = get_dependents(file)
        return {
            "file": file,
            "dependents": dependents,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/adrs")
def adrs_endpoint(file: str = Query(..., min_length=1)) -> dict:
    """Get architecture decisions affecting the given file."""
    if not file or not file.strip():
        raise HTTPException(status_code=400, detail="file parameter is required")

    try:
        adrs = get_adrs_for_file(file)
        return {
            "file": file,
            "adrs": adrs,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/report")
def report_endpoint(
    task: str = Query(..., min_length=1),
    _auth=Depends(require_auth)
) -> dict:
    """Generate a comprehensive markdown report for a task."""
    if not task or not task.strip():
        raise HTTPException(status_code=400, detail="task parameter is required")

    try:
        report = generate_report(task=task, repo_path=".")
        return {
            "task": task,
            "report": report,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cli-help")
def cli_help_endpoint() -> dict:
    """Get help for CLI commands."""
    return {
        "usage": "python -m src.cli.cli <command> [args]",
        "commands": [
            {
                "name": "index",
                "args": "<directory>",
                "description": "Index a directory: chunk, embed, build graph, load ADRs"
            },
            {
                "name": "search",
                "args": "<query> [--top-k N]",
                "description": "Search for relevant code chunks (default top-k=5)"
            },
            {
                "name": "ask",
                "args": "<task>",
                "description": "Ask the AI agent a question about the codebase"
            },
            {
                "name": "health",
                "args": "",
                "description": "Check health of all external services"
            },
            {
                "name": "cache-stats",
                "args": "",
                "description": "Show cache statistics (entries, hits)"
            },
            {
                "name": "cache-clear",
                "args": "",
                "description": "Clear all cached queries"
            },
            {
                "name": "deps",
                "args": "<file>",
                "description": "Show files that the given file imports"
            },
            {
                "name": "dependents",
                "args": "<file>",
                "description": "Show files that import the given file"
            },
            {
                "name": "adrs",
                "args": "<file>",
                "description": "Show architecture decisions affecting a file"
            },
            {
                "name": "git-log",
                "args": "<file>",
                "description": "Show git commit history for a file"
            }
        ]
    }

@app.get("/stream")
def stream_endpoint(
    task: str = Query(default=""),
    _auth=Depends(require_auth)
) -> StreamingResponse:
    """
    Stream LLM response as Server-Sent Events (SSE).
    """
    if not task or not task.strip():
        raise HTTPException(status_code=400, detail="task parameter is required")

    def generate():
        from src.agent.streaming_agent import stream_agent

        try:
            for token in stream_agent(task, "."):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/auth/keys")
def auth_generate_keys(body: dict) -> dict:
    """Generate a new API key."""
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name parameter is required")

    try:
        result = generate_api_key(name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/keys")
def auth_list_keys() -> dict:
    """List all API keys."""
    try:
        keys = list_api_keys()
        return {"keys": keys}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/auth/keys/{prefix}")
def auth_revoke_key(prefix: str) -> dict:
    """Revoke an API key by prefix."""
    try:
        success = revoke_api_key(prefix)
        if not success:
            raise HTTPException(status_code=404, detail="Key not found")
        return {"status": "revoked", "prefix": prefix}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/status")
def auth_status() -> dict:
    """Get authentication status."""
    try:
        keys = list_api_keys()
        active_keys = sum(1 for k in keys if k["is_active"])
        import os
        from pathlib import Path
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"

        return {
            "auth_enabled": auth_enabled,
            "total_keys": len(keys),
            "active_keys": active_keys,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
