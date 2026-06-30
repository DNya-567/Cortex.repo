from __future__ import annotations

import threading
import os
import traceback
from pathlib import Path
from urllib.parse import unquote

from fastapi import FastAPI, Query, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.search.searcher import search
from src.context.context_pack import assemble_context_pack
from src.agent.ollama_agent import query_agent
from src.agent.watcher import start_watcher
from src.health.checker import check_health
from src.cache.query_cache import get_cache_stats, clear_cache
from src.graph.import_resolver import get_dependencies, get_dependents, build_graph
from src.context.adr_store import get_adrs_for_file, load_adrs
from src.reporter.report import generate_report
from src.auth.middleware import require_auth
from src.auth.api_keys import generate_api_key, list_api_keys, revoke_api_key
from src.github.repo import get_repo_info, get_file_tree, get_file_tree_recursive, get_file_content
from src.github.indexer import index_github_repo
from src.github.pr_reader import list_pull_requests, get_pr_summary
from src.indexer import index_directory
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
        directory: str = Query("."),
        _auth=Depends(require_auth)
) -> dict:
    results = search(query=query, top_k=top_k, repo_path=directory)
    return {
        "query": query,
        "total": len(results),
        "results": results,
    }


@app.get("/context-pack")
def context_pack_endpoint(
        task: str = Query(..., min_length=1),
        directory: str = Query("."),
        _auth=Depends(require_auth)
) -> dict:
    """
    Assemble a comprehensive context pack for a given task.
    Returns chunks, dependencies, ADRs, and git history organized from least to most critical.
    """
    if not task or not task.strip():
        raise HTTPException(status_code=400, detail="task parameter is required and cannot be empty")

    try:
        context_pack = assemble_context_pack(task=task, repo_path=directory)
        return context_pack
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assemble context pack: {str(e)}"
        )


@app.get("/ask")
def ask_endpoint(
        task: str = Query(..., min_length=1),
        agent: str = Query("ollama"),
        directory: str = Query("."),
        _auth=Depends(require_auth)
) -> dict:
    """
    Query the AI agent with a task. Returns answer based on codebase context.
    agent can be: ollama, claude, openai, codex, groq, openrouter
    """
    if not task or not task.strip():
        raise HTTPException(status_code=400, detail="task parameter is required and cannot be empty")

    try:
        if agent == "ollama":
            result = query_agent(task=task, repo_path=directory)
        else:
            from src.context.context_pack import assemble_context_pack
            from src.orchestrator.agents import run_agent

            pack = assemble_context_pack(task=task, repo_path=directory)
            MAX_CHARS_PER_CHUNK = 800

            chunks_text = ""
            for chunk in pack.get("chunks", []):
                content = chunk.get("content", "")
                if len(content) > MAX_CHARS_PER_CHUNK:
                    content = content[:MAX_CHARS_PER_CHUNK] + "\n... (truncated for length)"
                chunks_text += f"\n--- {chunk.get('chunk_name')} ({chunk.get('file_path')}) ---\n"
                chunks_text += content + "\n"

            from src.agent.prompt_builder import pick_instruction
            instruction = pick_instruction(task)

            prompt = f"""TASK: {task}

=== RELEVANT CODE FROM CODEBASE ===
{chunks_text}

{instruction}"""
            agent_result = run_agent(agent, prompt, max_tokens=1500)
            result = {
                "task": task,
                "answer": agent_result.get("answer", ""),
                "error": agent_result.get("error"),
                "cached": False,
                "context_used": {"chunks": len(pack.get("chunks", []))}
            }
        return result
    except Exception as e:
        print(traceback.format_exc())
        return {
            "error": "Agent query failed",
            "message": str(e),
            "answer": "",
            "task": task
        }


@app.get("/index")
def index_endpoint(directory: str = Query("test-codebase")) -> dict:
    """
    Index a directory: chunk files, embed, and store in Qdrant.
    Also builds dependency graph and loads ADRs.
    """
    if not directory or not directory.strip():
        directory = "test-codebase"

    # Decode URL-encoded path (e.g., %5C becomes \)
    directory = unquote(directory)

    print(f"[API] /index called with directory: {directory}")

    # Check if directory exists
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"[API] Directory not found: {directory}")
        raise HTTPException(
            status_code=400,
            detail=f"Directory not found: {directory}"
        )

    if not dir_path.is_dir():
        print(f"[API] Path is not a directory: {directory}")
        raise HTTPException(
            status_code=400,
            detail=f"Path is not a directory: {directory}"
        )

    try:
        print(f"[API] Starting index of {directory}")

        # Index the directory
        index_result = index_directory(directory)

        # Build dependency graph
        build_graph(directory)

        # Load ADRs
        load_adrs("docs/adr")

        return {
            "status": "ok",
            "directory": directory,
            "total_files": index_result.get("total_files", 0),
            "total_chunks": index_result.get("total_chunks", 0),
        }
    except Exception as e:
        print(f"[API] Index failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Indexing failed: {str(e)}"
        )

@app.get("/index/progress")
def index_progress_endpoint() -> dict:
    """Poll this while indexing is running to get live progress."""
    from src.indexer import indexing_progress
    total = indexing_progress["total_chunks"]
    processed = indexing_progress["processed_chunks"]
    percent = round((processed / total) * 100, 1) if total > 0 else 0
    return {
        "active": indexing_progress["active"],
        "total_chunks": total,
        "processed_chunks": processed,
        "percent": percent,
        "current_file": indexing_progress["current_file"],
    }



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
        directory: str = Query("."),
        _auth=Depends(require_auth)
) -> dict:
    """Generate a comprehensive markdown report for a task."""
    if not task or not task.strip():
        raise HTTPException(status_code=400, detail="task parameter is required")

    try:
        report = generate_report(task=task, repo_path=directory)
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
        print(traceback.format_exc())
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


@app.get("/github/ask")
def github_ask_endpoint(
        task: str = Query(..., min_length=1),
        owner: str = Query(..., min_length=1),
        repo: str = Query(..., min_length=1),
        agent: str = Query("groq"),
) -> dict:
    """Ask a question about an already-indexed GitHub repo."""
    if not task or not task.strip():
        raise HTTPException(status_code=400, detail="task parameter is required")

    try:
        github_repo_path = f"github:{owner}/{repo}"

        if agent == "ollama":
            result = query_agent(task=task, repo_path=github_repo_path)
        else:
            from src.context.context_pack import assemble_context_pack
            from src.orchestrator.agents import run_agent
            from src.agent.prompt_builder import pick_instruction

            pack = assemble_context_pack(task=task, repo_path=github_repo_path)
            MAX_CHARS_PER_CHUNK = 800

            chunks_text = ""
            for chunk in pack.get("chunks", []):
                content = chunk.get("content", "")
                if len(content) > MAX_CHARS_PER_CHUNK:
                    content = content[:MAX_CHARS_PER_CHUNK] + "\n... (truncated for length)"
                chunks_text += f"\n--- {chunk.get('chunk_name')} ({chunk.get('file_path')}) ---\n"
                chunks_text += content + "\n"

            instruction = pick_instruction(task)
            prompt = f"""TASK: {task}

=== RELEVANT CODE FROM CODEBASE ===
{chunks_text}

{instruction}"""

            agent_result = run_agent(agent, prompt, max_tokens=1500)
            result = {
                "task": task,
                "answer": agent_result.get("answer", ""),
                "error": agent_result.get("error"),
                "cached": False,
                "context_used": {"chunks": len(pack.get("chunks", []))},
            }
        return result
    except Exception as e:
        print(traceback.format_exc())
        return {
            "error": "Agent query failed",
            "message": str(e),
            "answer": "",
            "task": task,
        }


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
    """Get list of available agents with details."""
    import os
    from src.orchestrator.agents import get_available_agents

    available_agents = get_available_agents()

    # Define all agents with their details
    agent_details = {
        "ollama": {
            "name": "ollama",
            "model": "llama3.2",
            "available": "ollama" in available_agents,
            "reason": None if "ollama" in available_agents else "Ollama not reachable"
        },
        "claude": {
            "name": "claude",
            "model": "claude-3-5-haiku-20241022",
            "available": "claude" in available_agents,
            "reason": None if "claude" in available_agents else "API key not configured"
        },
        "openai": {
            "name": "openai",
            "model": "gpt-3.5-turbo",
            "available": "openai" in available_agents,
            "reason": None if "openai" in available_agents else "API key not configured"
        },
        "groq": {
            "name": "groq",
            "model": "llama-3.1-8b-instant",
            "available": "groq" in available_agents,
            "reason": None if "groq" in available_agents else "API key not configured"
        },
        "openrouter": {
            "name": "openrouter",
            "model": "mistralai/mistral-7b-instruct:free",
            "available": "openrouter" in available_agents,
            "reason": None if "openrouter" in available_agents else "API key not configured"
        },
        "codex": {
            "name": "codex",
            "model": "gpt-3.5-turbo (code-focused)",
            "available": "codex" in available_agents,
            "reason": None if "codex" in available_agents else "API key not configured"
        }
    }

    agents_list = [
        {
            "name": details["name"],
            "model": details["model"],
            "available": details["available"],
            "reason": details["reason"]
        }
        for details in agent_details.values()
    ]

    return {"agents": agents_list, "total": len([a for a in agents_list if a["available"]])}


@app.get("/orchestrate")
def orchestrate_endpoint(
        task: str = Query(..., min_length=1),
        mode: str = Query("auto"),
        directory: str = Query(".")
) -> dict:
    """Run multi-agent orchestration pipeline."""
    if not task or not task.strip():
        raise HTTPException(status_code=400, detail="task parameter is required")

    try:
        from src.orchestrator.orchestrator import orchestrate
        result = orchestrate(task, mode=mode, repo_path=directory)
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
        agents: str = Query(None),
        directory: str = Query(".")
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

    result = compare_agents(task, agent_list, directory)
    return result


@app.post("/settings")
def save_settings(body: dict) -> dict:
    """Save API keys to .env file"""
    import os
    from pathlib import Path

    claude_key = body.get("claude_key", "")
    openai_key = body.get("openai_key", "")

    env_path = Path(".env")

    try:
        # Read existing .env content
        if env_path.exists():
            content = env_path.read_text(encoding="utf-8")
        else:
            content = ""

        # Update or add keys
        lines = content.split("\n")
        updated_lines = []
        claude_found = False
        openai_found = False

        for line in lines:
            if line.startswith("ANTHROPIC_API_KEY="):
                if claude_key:
                    updated_lines.append(f"ANTHROPIC_API_KEY={claude_key}")
                    claude_found = True
                # Skip if we're clearing the key
            elif line.startswith("OPENAI_API_KEY="):
                if openai_key:
                    updated_lines.append(f"OPENAI_API_KEY={openai_key}")
                    openai_found = True
                # Skip if we're clearing the key
            else:
                if line.strip():  # Keep non-empty lines
                    updated_lines.append(line)

        # Add new keys if they weren't found
        if claude_key and not claude_found:
            updated_lines.append(f"ANTHROPIC_API_KEY={claude_key}")
        if openai_key and not openai_found:
            updated_lines.append(f"OPENAI_API_KEY={openai_key}")

        # Write back to .env
        new_content = "\n".join(updated_lines)
        if new_content and not new_content.endswith("\n"):
            new_content += "\n"

        env_path.write_text(new_content, encoding="utf-8")

        # Also update os.environ so changes take effect immediately
        if claude_key:
            os.environ["ANTHROPIC_API_KEY"] = claude_key
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key

        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {str(e)}")


@app.get("/dashboard")
def serve_dashboard():
    """Serve dashboard at http://localhost:8000/dashboard"""
    return FileResponse("dashboard_phase13.html")
