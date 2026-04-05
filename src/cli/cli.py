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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()

