from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.indexer import index_directory
from src.graph.import_resolver import build_graph, get_dependencies, get_dependents
from src.context.adr_store import load_adrs, get_adrs_for_file
from src.context.git_log import get_file_history
from src.search.searcher import search
from src.agent.ollama_agent import query_agent
from src.health.checker import check_health
from src.cache.query_cache import get_cache_stats, clear_cache
from src.chunker.chunk_stats import get_chunk_stats
from src.auth.api_keys import generate_api_key, list_api_keys, revoke_api_key
from src.github.repo import get_file_tree, get_file_tree_recursive, get_file_content
from src.github.indexer import index_github_repo
from src.github.pr_reader import list_pull_requests, get_pr_summary


def cmd_index(args) -> None:
    """Index a directory: chunk, embed, build graph, load ADRs."""
    directory = args.directory
    try:
        print(f"Indexing {directory}...")
        result = index_directory(directory)
        print(f"✓ Indexed {result['total_chunks']} chunks from {result['total_files']} files")

        print("Building dependency graph...")
        build_graph(directory)
        print("✓ Dependency graph built")

        print("Loading ADRs...")
        load_adrs("docs/adr")
        print("✓ ADRs loaded")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_search(args) -> None:
    """Search for relevant code chunks."""
    query_text = args.query
    top_k = args.top_k
    try:
        results = search(query_text, top_k=top_k)
        if not results:
            print("No results found.")
            return

        for i, result in enumerate(results, 1):
            score = result.get("score", 0.0)
            name = result.get("chunk_name", "")
            file = result.get("file_path", "")
            start = result.get("start_line", 0)
            end = result.get("end_line", 0)
            content = result.get("content", "")

            content_preview = content.replace("\n", " ")[:100]
            print(f"{i}. [score: {score:.2f}] {name} @ {file} (lines {start}-{end})")
            print(f"   {content_preview}...\n")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_ask(args) -> None:
    """Ask the AI agent a question about the codebase."""
    task = args.task
    try:
        result = query_agent(task, ".")
        cached = result.get("cached", False)
        answer = result.get("answer", "")
        context = result.get("context_used", {})

        if cached:
            print("[CACHED] ", end="")
        print(f"Answer to: {task}\n")
        print(answer)
        print(f"\nContext: {context['chunks']} chunks, {context['adrs']} ADRs, {context['dependencies']} deps")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_health(args) -> None:
    """Check health of all external services."""
    try:
        health = check_health()
        print("System Health:\n")

        for service in ["ollama", "qdrant", "qdrant_collection", "sqlite"]:
            status_data = health.get(service, {})
            status = status_data.get("status", "unknown")
            message = status_data.get("message", "")
            symbol = "✓" if status == "ok" else "✗"
            print(f"{symbol} {service}: {message}")

        overall = health.get("overall", "unknown")
        print(f"\nOverall: {overall}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_cache_stats(args) -> None:
    """Show cache statistics."""
    try:
        stats = get_cache_stats()
        entries = stats.get("total_entries", 0)
        hits = stats.get("total_hits", 0)
        print(f"Cached queries: {entries} | Total hits: {hits}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_cache_clear(args) -> None:
    """Clear the query cache."""
    try:
        clear_cache()
        print("Cache cleared.")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_deps(args) -> None:
    """Show dependencies of a file."""
    file_path = args.file
    try:
        deps = get_dependencies(file_path)
        if not deps:
            print(f"No dependencies found for {file_path}")
            return

        print(f"Dependencies of {file_path}:")
        for dep in deps:
            imported = dep.get("imported_file", "")
            names = dep.get("imported_names", "")
            print(f"  → {imported}  [{names}]")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_dependents(args) -> None:
    """Show files that import the given file."""
    file_path = args.file
    try:
        dependents = get_dependents(file_path)
        if not dependents:
            print(f"No files import {file_path}")
            return

        print(f"Files that import {file_path}:")
        for dependent in dependents:
            source = dependent.get("source_file", "")
            print(f"  ← {source}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_adrs(args) -> None:
    """Show ADRs affecting a file."""
    file_path = args.file
    try:
        adrs = get_adrs_for_file(file_path)
        if not adrs:
            print(f"No ADRs found for {file_path}")
            return

        print(f"Architecture Decisions affecting {file_path}:")
        for adr in adrs:
            adr_id = adr.get("adr_id", "")
            title = adr.get("title", "")
            decision = adr.get("decision", "")[:100]
            print(f"  [{adr_id}] {title}")
            print(f"      {decision}...\n")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_git_log(args) -> None:
    """Show git history for a file."""
    file_path = args.file
    try:
        commits = get_file_history(".", file_path)
        if not commits:
            print(f"No git history found for {file_path}")
            return

        print(f"Git history for {file_path}:")
        for commit in commits:
            hash_str = commit.get("commit_hash", "")
            date = commit.get("date", "")
            author = commit.get("author_name", "")
            message = commit.get("message", "")
            print(f"  {hash_str} | {date} | {author} | {message}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_chunk_stats(args) -> None:
    """Show chunking statistics for a directory."""
    directory = args.directory
    try:
        stats = get_chunk_stats(directory)
        print(f"Chunking Statistics for {directory}:\n")
        print(f"Total chunks: {stats['total_chunks']}")
        print(f"Files processed: {stats['files_processed']}")
        print(f"Average chunk size: {stats['avg_chunk_size_lines']} lines\n")

        print("By Language:")
        for lang, count in sorted(stats['by_language'].items()):
            print(f"  {lang}: {count}")

        print("\nBy Type:")
        for ctype, count in sorted(stats['by_type'].items()):
            print(f"  {ctype}: {count}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_key_generate(args) -> None:
    """Generate a new API key."""
    name = args.name
    try:
        result = generate_api_key(name)
        print("API Key generated!")
        print(f"Key:     {result['key']}")
        print(f"Prefix:  {result['prefix']}")
        print(f"Name:    {result['name']}")
        print(f"Created: {result['created_at']}")
        print("\nIMPORTANT: Save this key. It will not be shown again.")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_key_list(args) -> None:
    """List all API keys."""
    try:
        keys = list_api_keys()
        if not keys:
            print("No API keys found.")
            return

        print(f"{'PREFIX':<12} {'NAME':<20} {'CREATED':<19} {'REQUESTS':<10} {'ACTIVE':<6}")
        print("-" * 70)
        for key in keys:
            active = "yes" if key["is_active"] else "no"
            print(f"{key['prefix']:<12} {key['name']:<20} {key['created_at']:<19} {key['request_count']:<10} {active:<6}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_key_revoke(args) -> None:
    """Revoke an API key."""
    prefix = args.prefix
    try:
        success = revoke_api_key(prefix)
        if success:
            print(f"Key {prefix} revoked.")
        else:
            print("Key not found.")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_gh_tree(args) -> None:
    """Explore GitHub repository file tree."""
    owner = args.owner
    repo = args.repo
    branch = args.branch
    path = args.path

    try:
        tree = get_file_tree(owner, repo, branch, path)

        for item in tree:
            if item["type"] == "dir":
                print(f"📁 {item['name']}/")
            else:
                size_kb = item.get("size", 0) / 1024
                print(f"📄 {item['name']} ({size_kb:.1f} KB)")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_gh_file(args) -> None:
    """Get content of a GitHub file."""
    owner = args.owner
    repo = args.repo
    path = args.path
    branch = args.branch

    try:
        result = get_file_content(owner, repo, path, branch)
        print(f"File: {result['path']}")
        print(f"Language: {result['language']}")
        print(f"Lines: {result['lines']}")
        print("---")
        print(result['content'])
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_gh_index(args) -> None:
    """Index a GitHub repository into Qdrant."""
    owner = args.owner
    repo = args.repo
    branch = args.branch

    try:
        print(f"Indexing {owner}/{repo} ({branch})...")
        result = index_github_repo(owner, repo, branch)
        print(f"✓ Indexed {result['total_chunks']} chunks from {result['total_files']} files")
        if result['skipped_files'] > 0:
            print(f"⚠ Skipped {result['skipped_files']} files")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_gh_prs(args) -> None:
    """List pull requests for a GitHub repository."""
    owner = args.owner
    repo = args.repo
    state = args.state

    try:
        prs = list_pull_requests(owner, repo, state, limit=20)
        if not prs:
            print("No pull requests found.")
            return

        print(f"{' #':<5} {'Title':<50} {'Author':<15} {'State':<10}")
        print("-" * 80)
        for pr in prs:
            print(f"#{pr.get('number'):<4} {pr.get('title', ''):<50} "
                  f"{pr.get('author', ''):<15} {pr.get('state', ''):<10}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_gh_pr(args) -> None:
    """Get detailed PR information."""
    owner = args.owner
    repo = args.repo
    number = args.number

    try:
        result = get_pr_summary(owner, repo, number)
        pr = result["pr"]

        print(f"PR #{pr['number']}: {pr['title']}")
        print(f"State: {pr['state']} | Author: {pr['author']}")
        print(f"Branch: {pr['branch']} → {pr['base']}")
        print(f"Created: {pr['created_at']} | Updated: {pr['updated_at']}")
        print()
        print(f"Body:\n{pr['body']}")
        print()
        print(f"Diff Summary: {result['diff_summary']}")

        if result['files_changed']:
            print("\nFiles changed:")
            for file in result['files_changed']:
                print(f"  {file['filename']} (+{file['additions']} -{file['deletions']})")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_orchestrate(args) -> None:
    """Run multi-agent orchestration."""
    task = args.task
    mode = getattr(args, 'mode', 'auto')
    try:
        from src.orchestrator.orchestrator import orchestrate

        print(f"Orchestrating task: {task}")
        print(f"Mode: {mode}")
        print()

        result = orchestrate(task, mode=mode, repo_path=".")

        # Print subtask results
        for i, subtask in enumerate(result.get("subtasks", []), 1):
            agent = subtask.get("agent", "unknown")
            duration = subtask.get("duration_ms", 0)
            print(f"[{i}/{len(result.get('subtasks', []))}] {agent}: {subtask['description']}")
            if subtask.get("error"):
                print(f"  ✗ ERROR: {subtask['error']}")
            else:
                preview = subtask.get("answer", "")[:200]
                print(f"  ✓ {preview}...")
            print(f"  Duration: {duration}ms")
            print()

        # Print final answer
        print("="*60)
        print("FINAL ANSWER:")
        print("="*60)
        print(result.get("final_answer", ""))
        print()

        # Print summary
        print("="*60)
        print(f"Run ID: {result.get('run_id')}")
        print(f"Duration: {result.get('total_duration_ms', 0)/1000:.1f}s")
        print(f"Agents used: {', '.join(result.get('agents_used', []))}")
        context = result.get("context_used", {})
        print(f"Context: {context.get('chunks', 0)} chunks, "
              f"{context.get('adrs', 0)} ADRs, "
              f"{context.get('git_commits', 0)} commits")
        print("="*60)

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_orchestrate_github(args) -> None:
    """Orchestrate on GitHub repository."""
    owner = args.owner
    repo = args.repo
    task = args.task
    branch = getattr(args, 'branch', 'main')
    mode = getattr(args, 'mode', 'auto')
    try:
        from src.orchestrator.orchestrator import orchestrate_github

        print(f"Orchestrating task on {owner}/{repo} ({branch})")
        print(f"Task: {task}")
        print(f"Mode: {mode}")
        print()

        result = orchestrate_github(task, owner, repo, branch=branch, mode=mode)

        # Print subtask results
        for i, subtask in enumerate(result.get("subtasks", []), 1):
            agent = subtask.get("agent", "unknown")
            duration = subtask.get("duration_ms", 0)
            print(f"[{i}/{len(result.get('subtasks', []))}] {agent}: {subtask['description']}")
            if subtask.get("error"):
                print(f"  ✗ ERROR: {subtask['error']}")
            else:
                preview = subtask.get("answer", "")[:200]
                print(f"  ✓ {preview}...")
            print(f"  Duration: {duration}ms")
            print()

        # Print final answer
        print("="*60)
        print("FINAL ANSWER:")
        print("="*60)
        print(result.get("final_answer", ""))
        print()

        # Print summary
        print("="*60)
        print(f"Run ID: {result.get('run_id')}")
        print(f"Duration: {result.get('total_duration_ms', 0)/1000:.1f}s")
        print(f"Agents used: {', '.join(result.get('agents_used', []))}")
        print("="*60)

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_agents(args) -> None:
    """List available agents."""
    try:
        from src.orchestrator.agents import get_available_agents
        import os

        available = get_available_agents()

        print("Available Agents:")
        print()

        if "ollama" in available:
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            print(f"✓ ollama")
            print(f"    Running at: {ollama_url}")
            print(f"    Model: {os.getenv('OLLAMA_CHAT_MODEL', 'llama3.2')}")
        else:
            print("✗ ollama  (Ollama not running)")

        if "claude" in available:
            print("✓ claude")
            print("    Model: claude-3-5-haiku-20241022")
        else:
            print("✗ claude  (ANTHROPIC_API_KEY not set)")

        if "openai" in available:
            print("✓ openai")
            print("    Model: gpt-4o-mini")
        else:
            print("✗ openai  (OPENAI_API_KEY not set)")

        if "codex" in available:
            print("✓ codex")
            print("    Model: gpt-4o-mini (code-focused)")
        else:
            print("✗ codex   (OPENAI_API_KEY not set)")

        print()
        print(f"Total available: {len(available)}")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_history(args) -> None:
    """Show orchestration history."""
    limit = getattr(args, 'limit', 20)
    try:
        from src.orchestrator.history import list_runs

        runs = list_runs(limit=limit)

        if not runs:
            print("No orchestration runs found.")
            return

        print(f"Orchestration History (last {len(runs)} runs):")
        print()

        # Table header
        print(f"{'RUN ID':<8} | {'TASK':<30} | {'MODE':<10} | {'SUBTASKS':<8} | {'AGENTS':<20} | {'DATE':<19}")
        print("-" * 120)

        for run in runs:
            run_id = run["run_id"]
            task = run["task"][:27] + "..." if len(run["task"]) > 30 else run["task"]
            mode = run.get("mode", "auto")
            subtasks = run.get("subtask_count", 0)
            agents = ", ".join(run.get("agents_used", []))[:17] + ".." if len(", ".join(run.get("agents_used", []))) > 19 else ", ".join(run.get("agents_used", []))
            created = run.get("created_at", "")[:19]

            print(f"{run_id:<8} | {task:<30} | {mode:<10} | {subtasks:<8} | {agents:<20} | {created:<19}")

        print()

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_history_get(args) -> None:
    """Get details of an orchestration run."""
    run_id = args.run_id
    try:
        from src.orchestrator.history import get_run

        run = get_run(run_id)
        if not run:
            print(f"Run {run_id} not found.")
            sys.exit(1)

        print(f"Orchestration Run: {run_id}")
        print("="*60)
        print()

        print(f"Task: {run['task']}")
        print(f"Mode: {run.get('mode', 'auto')}")
        print(f"Created: {run.get('created_at', 'unknown')}")
        print(f"Duration: {run.get('total_duration_ms', 0)/1000:.1f}s")
        print(f"Agents: {', '.join(run.get('agents_used', []))}")
        print()

        print("Subtasks:")
        print("-"*60)
        for subtask in run.get("subtasks", []):
            print()
            print(f"  [{subtask['subtask_id']}] {subtask['description']}")
            print(f"      Agent: {subtask['agent']}")
            print(f"      Duration: {subtask.get('duration_ms', 0)}ms")
            if subtask.get("error"):
                print(f"      Error: {subtask['error']}")
            else:
                answer_preview = subtask.get("answer", "")[:150]
                print(f"      Answer: {answer_preview}...")

        print()
        print("="*60)
        print("Final Answer:")
        print("="*60)
        print(run.get("final_answer", ""))

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Context Engine CLI - AI-native codebase analysis",
        prog="python -m src.cli.cli"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # index <directory>
    index_parser = subparsers.add_parser("index", help="Index a directory")
    index_parser.add_argument("directory", help="Directory to index")
    index_parser.set_defaults(func=cmd_index)

    # search <query> [--top-k N]
    search_parser = subparsers.add_parser("search", help="Search for code")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    search_parser.set_defaults(func=cmd_search)

    # ask <task>
    ask_parser = subparsers.add_parser("ask", help="Ask the AI agent")
    ask_parser.add_argument("task", help="Task description")
    ask_parser.set_defaults(func=cmd_ask)

    # health
    health_parser = subparsers.add_parser("health", help="Check system health")
    health_parser.set_defaults(func=cmd_health)

    # cache-stats
    cache_stats_parser = subparsers.add_parser("cache-stats", help="Show cache stats")
    cache_stats_parser.set_defaults(func=cmd_cache_stats)

    # cache-clear
    cache_clear_parser = subparsers.add_parser("cache-clear", help="Clear cache")
    cache_clear_parser.set_defaults(func=cmd_cache_clear)

    # deps <file>
    deps_parser = subparsers.add_parser("deps", help="Show file dependencies")
    deps_parser.add_argument("file", help="File path")
    deps_parser.set_defaults(func=cmd_deps)

    # dependents <file>
    dependents_parser = subparsers.add_parser("dependents", help="Show file dependents")
    dependents_parser.add_argument("file", help="File path")
    dependents_parser.set_defaults(func=cmd_dependents)

    # adrs <file>
    adrs_parser = subparsers.add_parser("adrs", help="Show ADRs for file")
    adrs_parser.add_argument("file", help="File path")
    adrs_parser.set_defaults(func=cmd_adrs)

    # git-log <file>
    git_log_parser = subparsers.add_parser("git-log", help="Show git history")
    git_log_parser.add_argument("file", help="File path")
    git_log_parser.set_defaults(func=cmd_git_log)

    # chunk-stats <directory>
    chunk_stats_parser = subparsers.add_parser("chunk-stats", help="Show chunking stats")
    chunk_stats_parser.add_argument("directory", help="Directory to analyze")
    chunk_stats_parser.set_defaults(func=cmd_chunk_stats)

    # key-generate <name>
    key_generate_parser = subparsers.add_parser("key-generate", help="Generate a new API key")
    key_generate_parser.add_argument("name", help="Name for the API key")
    key_generate_parser.set_defaults(func=cmd_key_generate)

    # key-list
    key_list_parser = subparsers.add_parser("key-list", help="List all API keys")
    key_list_parser.set_defaults(func=cmd_key_list)

    # key-revoke <prefix>
    key_revoke_parser = subparsers.add_parser("key-revoke", help="Revoke an API key")
    key_revoke_parser.add_argument("prefix", help="Prefix of the API key to revoke")
    key_revoke_parser.set_defaults(func=cmd_key_revoke)

    # gh-tree <owner> <repo>
    gh_tree_parser = subparsers.add_parser("gh-tree", help="Explore GitHub repo file tree")
    gh_tree_parser.add_argument("owner", help="GitHub username")
    gh_tree_parser.add_argument("repo", help="Repository name")
    gh_tree_parser.add_argument("--branch", default="main", help="Branch name")
    gh_tree_parser.add_argument("--path", default="", help="Directory path")
    gh_tree_parser.set_defaults(func=cmd_gh_tree)

    # gh-file <owner> <repo> <path>
    gh_file_parser = subparsers.add_parser("gh-file", help="Get GitHub file content")
    gh_file_parser.add_argument("owner", help="GitHub username")
    gh_file_parser.add_argument("repo", help="Repository name")
    gh_file_parser.add_argument("path", help="File path")
    gh_file_parser.add_argument("--branch", default="main", help="Branch name")
    gh_file_parser.set_defaults(func=cmd_gh_file)

    # gh-index <owner> <repo>
    gh_index_parser = subparsers.add_parser("gh-index", help="Index GitHub repo")
    gh_index_parser.add_argument("owner", help="GitHub username")
    gh_index_parser.add_argument("repo", help="Repository name")
    gh_index_parser.add_argument("--branch", default="main", help="Branch name")
    gh_index_parser.set_defaults(func=cmd_gh_index)

    # gh-prs <owner> <repo>
    gh_prs_parser = subparsers.add_parser("gh-prs", help="List GitHub PRs")
    gh_prs_parser.add_argument("owner", help="GitHub username")
    gh_prs_parser.add_argument("repo", help="Repository name")
    gh_prs_parser.add_argument("--state", default="open", help="PR state (open/closed/all)")
    gh_prs_parser.set_defaults(func=cmd_gh_prs)

    # gh-pr <owner> <repo> <number>
    gh_pr_parser = subparsers.add_parser("gh-pr", help="Get GitHub PR details")
    gh_pr_parser.add_argument("owner", help="GitHub username")
    gh_pr_parser.add_argument("repo", help="Repository name")
    gh_pr_parser.add_argument("number", type=int, help="PR number")
    gh_pr_parser.set_defaults(func=cmd_gh_pr)

    # orchestrate <task>
    orchestrate_parser = subparsers.add_parser("orchestrate", help="Run multi-agent orchestration")
    orchestrate_parser.add_argument("task", help="Task to orchestrate")
    orchestrate_parser.add_argument("--mode", default="auto", help="Agent mode (auto/ollama/claude/openai/codex/collaborative)")
    orchestrate_parser.set_defaults(func=cmd_orchestrate)

    # orchestrate-github <owner> <repo> <task>
    orchestrate_github_parser = subparsers.add_parser("orchestrate-github", help="Orchestrate on GitHub repo")
    orchestrate_github_parser.add_argument("owner", help="GitHub username")
    orchestrate_github_parser.add_argument("repo", help="Repository name")
    orchestrate_github_parser.add_argument("task", help="Task to orchestrate")
    orchestrate_github_parser.add_argument("--branch", default="main", help="Branch name")
    orchestrate_github_parser.add_argument("--mode", default="auto", help="Agent mode")
    orchestrate_github_parser.set_defaults(func=cmd_orchestrate_github)

    # agents
    agents_parser = subparsers.add_parser("agents", help="List available agents")
    agents_parser.set_defaults(func=cmd_agents)

    # history
    history_parser = subparsers.add_parser("history", help="Show orchestration history")
    history_parser.add_argument("--limit", type=int, default=10, help="Limit number of runs")
    history_parser.set_defaults(func=cmd_history)

    # history-get <run_id>
    history_get_parser = subparsers.add_parser("history-get", help="Get orchestration run details")
    history_get_parser.add_argument("run_id", help="Run ID")
    history_get_parser.set_defaults(func=cmd_history_get)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()

