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
from src.github.repo import get_repo_info, get_file_tree, get_file_tree_recursive, get_file_content
from src.github.indexer import index_github_repo
from src.github.pr_reader import list_pull_requests, get_pr_summary
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Context Engine Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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


# ============================================================================
# GitHub Integration Endpoints
# ============================================================================

@app.get("/github/repo")
def github_repo_endpoint(
    owner: str = Query(..., min_length=1),
    repo: str = Query(..., min_length=1)
) -> dict:
    """Get GitHub repository metadata."""
    try:
        return get_repo_info(owner, repo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/github/tree")
def github_tree_endpoint(
    owner: str = Query(..., min_length=1),
    repo: str = Query(..., min_length=1),
    path: str = Query(""),
    branch: str = Query("main")
) -> dict:
    """Get file tree for a repository path."""
    try:
        tree = get_file_tree(owner, repo, branch, path)
        return {
            "owner": owner,
            "repo": repo,
            "path": path,
            "tree": tree,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/github/tree/recursive")
def github_tree_recursive_endpoint(
    owner: str = Query(..., min_length=1),
    repo: str = Query(..., min_length=1),
    branch: str = Query("main"),
    depth: int = Query(3, ge=1, le=10)
) -> dict:
    """Get recursive file tree for a repository."""
    try:
        tree = get_file_tree_recursive(owner, repo, branch, "", depth)
        return {
            "owner": owner,
            "repo": repo,
            "tree": tree,
            "total": len(tree),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/github/file")
def github_file_endpoint(
    owner: str = Query(..., min_length=1),
    repo: str = Query(..., min_length=1),
    path: str = Query(..., min_length=1),
    branch: str = Query("main")
) -> dict:
    """Get file content from a repository."""
    try:
        return get_file_content(owner, repo, path, branch)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/github/index")
def github_index_endpoint(
    owner: str = Query(..., min_length=1),
    repo: str = Query(..., min_length=1),
    branch: str = Query("main")
) -> dict:
    """Index a GitHub repository into Qdrant."""
    try:
        return index_github_repo(owner, repo, branch)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/github/prs")
def github_prs_endpoint(
    owner: str = Query(..., min_length=1),
    repo: str = Query(..., min_length=1),
    state: str = Query("open")
) -> dict:
    """List pull requests for a repository."""
    try:
        prs = list_pull_requests(owner, repo, state, limit=20)
        return {
            "owner": owner,
            "repo": repo,
            "state": state,
            "prs": prs,
            "total": len(prs),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/github/pr")
def github_pr_endpoint(
    owner: str = Query(..., min_length=1),
    repo: str = Query(..., min_length=1),
    number: int = Query(..., ge=1)
) -> dict:
    """Get detailed PR summary with diff."""
    try:
        return get_pr_summary(owner, repo, number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ORCHESTRATOR ENDPOINTS ====================

@app.get("/orchestrate/agents")
def orchestrate_agents_endpoint() -> dict:
    """Get list of available agents."""
    from src.orchestrator.agents import get_available_agents
    agents = get_available_agents()
    return {"agents": agents, "total": len(agents)}


@app.get("/orchestrate")
def orchestrate_endpoint(
    task: str = Query(..., min_length=1),
    mode: str = Query("auto")
) -> dict:
    """Run multi-agent orchestration pipeline."""
    if not task or not task.strip():
        raise HTTPException(status_code=400, detail="task parameter is required")

    try:
        from src.orchestrator.orchestrator import orchestrate
        result = orchestrate(task, mode=mode, repo_path=".")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orchestrate/github")
def orchestrate_github_endpoint(
    task: str = Query(..., min_length=1),
    owner: str = Query(..., min_length=1),
    repo: str = Query(..., min_length=1),
    branch: str = Query("main"),
    mode: str = Query("auto")
) -> dict:
    """Run orchestration on a GitHub repository."""
    if not task or not task.strip():
        raise HTTPException(status_code=400, detail="task parameter is required")

    try:
        from src.orchestrator.orchestrator import orchestrate_github
        result = orchestrate_github(task, owner, repo, branch=branch, mode=mode)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orchestrate/history")
def orchestrate_history_endpoint(limit: int = Query(20, ge=1, le=100)) -> dict:
    """Get orchestration run history."""
    from src.orchestrator.history import list_runs
    runs = list_runs(limit=limit)
    return {"runs": runs, "total": len(runs)}


@app.get("/orchestrate/history/{run_id}")
def orchestrate_history_get_endpoint(run_id: str) -> dict:
    """Get specific orchestration run details."""
    from src.orchestrator.history import get_run
    result = get_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return result


@app.delete("/orchestrate/history/{run_id}")
def orchestrate_history_delete_endpoint(run_id: str) -> dict:
    """Delete an orchestration run."""
    from src.orchestrator.history import delete_run
    if delete_run(run_id):
        return {"status": "deleted", "run_id": run_id}
    else:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")


@app.get("/recommend")
def recommend_endpoint(task: str = Query(..., min_length=1)) -> dict:
    """Recommend the best agent for a task."""
    from src.orchestrator.agents import get_available_agents
    from src.orchestrator.selector import recommend_agent

    available = get_available_agents()
    recommendation = recommend_agent(task, available)
    return recommendation


@app.get("/compare")
def compare_endpoint(
    task: str = Query(..., min_length=1),
    agents: str = Query(None)
) -> dict:
    """Compare multiple agents on the same task."""
    from src.orchestrator.agents import get_available_agents
    from src.orchestrator.comparator import compare_agents

    # Parse agents parameter
    if agents:
        agent_list = [a.strip() for a in agents.split(",") if a.strip()]
    else:
        agent_list = get_available_agents()

    if not agent_list:
        agent_list = ["ollama"]  # Fallback to ollama

    result = compare_agents(task, agent_list, ".")
    return result

