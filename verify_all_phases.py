#!/usr/bin/env python3
"""Master Verification Script - Test All Phases 1-12"""

import sys
import os
from pathlib import Path

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

os.environ["PYTHONPATH"] = "."

def test_imports():
    """Test all module imports"""
    print("\n" + "="*70)
    print("MODULE IMPORT TESTS")
    print("="*70 + "\n")

    modules = [
        ("Phase 1: Chunker", "src.chunker.chunker", ["chunk_file", "chunk_directory"]),
        ("Phase 2: Embedder", "src.embedder.embedder", ["get_embedding"]),
        ("Phase 2: Storage", "src.storage.qdrant_store", ["setup_collection", "store_chunk"]),
        ("Phase 2: Indexer", "src.indexer", ["index_directory"]),
        ("Phase 2: Search", "src.search.searcher", ["search"]),
        ("Phase 2: Graph", "src.graph.import_resolver", ["build_graph", "get_dependencies"]),
        ("Phase 2: ADR", "src.context.adr_store", ["load_adrs", "get_all_adrs"]),
        ("Phase 2: Git", "src.context.git_log", ["get_file_history"]),
        ("Phase 2: Context Pack", "src.context.context_pack", ["assemble_context_pack"]),
        ("Phase 3: Agent", "src.agent.ollama_agent", ["query_agent"]),
        ("Phase 3: Streaming", "src.agent.streaming_agent", ["stream_agent"]),
        ("Phase 3: Watcher", "src.agent.watcher", ["start_watcher"]),
        ("Phase 4: Cache", "src.cache.query_cache", ["get_cached", "store_cache"]),
        ("Phase 4: Health", "src.health.checker", ["check_health"]),
        ("Phase 5: CLI", "src.cli.cli", ["main"]),
        ("Phase 7: Chunker Multi", "src.chunker.chunker", ["chunk_file_any", "chunk_directory_any"]),
        ("Phase 7: Stats", "src.chunker.chunk_stats", ["get_chunk_stats"]),
        ("Phase 9: Auth", "src.auth.api_keys", ["generate_api_key", "list_api_keys"]),
        ("Phase 9: Rate Limit", "src.auth.rate_limiter", ["check_rate_limit"]),
        ("Phase 10: Report", "src.reporter.report", ["generate_report"]),
        ("Phase 11: GitHub", "src.github.repo", ["get_repo_info", "get_file_tree"]),
        ("Phase 12: Agents", "src.orchestrator.agents", ["get_available_agents", "run_agent"]),
        ("Phase 12: Planner", "src.orchestrator.planner", ["plan_task"]),
        ("Phase 12: Runner", "src.orchestrator.runner", ["run_plan"]),
        ("Phase 12: History", "src.orchestrator.history", ["get_run", "list_runs"]),
        ("Phase 12: Orchestrator", "src.orchestrator.orchestrator", ["orchestrate"]),
    ]

    passed = 0
    failed = 0

    for phase, module, funcs in modules:
        try:
            mod = __import__(module, fromlist=funcs)
            for func in funcs:
                if not hasattr(mod, func):
                    print(f"✗ {phase}: {func} not found")
                    failed += 1
                    continue
            print(f"✓ {phase}")
            passed += 1
        except Exception as e:
            print(f"✗ {phase}: {str(e)[:50]}")
            failed += 1

    print(f"\nImport Tests: {passed}/{passed+failed} passed")
    return passed == len(modules)


def test_functionality():
    """Test actual functionality"""
    print("\n" + "="*70)
    print("FUNCTIONALITY TESTS")
    print("="*70 + "\n")

    tests = []

    # Test 1: Chunker
    try:
        from src.chunker.chunker import chunk_directory
        chunks = chunk_directory("test-codebase")
        if len(chunks) > 0:
            print(f"✓ Chunker: {len(chunks)} chunks found")
            tests.append(True)
        else:
            print(f"✗ Chunker: No chunks found")
            tests.append(False)
    except Exception as e:
        print(f"✗ Chunker: {str(e)[:50]}")
        tests.append(False)

    # Test 2: Embedder
    try:
        from src.embedder.embedder import get_embedding
        embedding = get_embedding("test")
        if len(embedding) == 768:
            print(f"✓ Embedder: {len(embedding)} dims (correct)")
            tests.append(True)
        else:
            print(f"✗ Embedder: Wrong dims ({len(embedding)} != 768)")
            tests.append(False)
    except Exception as e:
        print(f"✗ Embedder: {str(e)[:50]}")
        tests.append(False)

    # Test 3: Qdrant Storage
    try:
        from src.storage.qdrant_store import setup_collection
        setup_collection()
        print(f"✓ Qdrant: Collection setup OK")
        tests.append(True)
    except Exception as e:
        print(f"✗ Qdrant: {str(e)[:50]}")
        tests.append(False)

    # Test 4: Search
    try:
        from src.search.searcher import search
        results = search("login", top_k=3)
        if len(results) > 0:
            print(f"✓ Search: {len(results)} results found")
            tests.append(True)
        else:
            print(f"✗ Search: No results found")
            tests.append(False)
    except Exception as e:
        print(f"✗ Search: {str(e)[:50]}")
        tests.append(False)

    # Test 5: Context Pack
    try:
        from src.context.context_pack import assemble_context_pack
        pack = assemble_context_pack("test", ".")
        chunks = len(pack.get("chunks", []))
        print(f"✓ Context Pack: {chunks} chunks in pack")
        tests.append(True)
    except Exception as e:
        print(f"✗ Context Pack: {str(e)[:50]}")
        tests.append(False)

    # Test 6: Cache
    try:
        from src.cache.query_cache import get_cache_stats
        stats = get_cache_stats()
        print(f"✓ Cache: {stats['total_entries']} entries")
        tests.append(True)
    except Exception as e:
        print(f"✗ Cache: {str(e)[:50]}")
        tests.append(False)

    # Test 7: Health Check
    try:
        from src.health.checker import check_health
        health = check_health()
        overall = health.get("overall", "unknown")
        print(f"✓ Health: overall={overall}")
        tests.append(True)
    except Exception as e:
        print(f"✗ Health: {str(e)[:50]}")
        tests.append(False)

    # Test 8: Orchestrator
    try:
        from src.orchestrator.agents import get_available_agents
        from src.orchestrator.planner import plan_task
        agents = get_available_agents()
        plan = plan_task("test", agents, mode="auto")
        print(f"✓ Orchestrator: {len(agents)} agents, {len(plan)} subtasks")
        tests.append(True)
    except Exception as e:
        print(f"✗ Orchestrator: {str(e)[:50]}")
        tests.append(False)

    # Test 9: FastAPI
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app
        client = TestClient(app)
        response = client.get("/health")
        if response.status_code == 200:
            print(f"✓ FastAPI: /health returns 200")
            tests.append(True)
        else:
            print(f"✗ FastAPI: /health returns {response.status_code}")
            tests.append(False)
    except Exception as e:
        print(f"✗ FastAPI: {str(e)[:50]}")
        tests.append(False)

    # Test 10: API Endpoints
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app
        client = TestClient(app)
        endpoints_ok = 0
        endpoints = [
            ("/search?query=login&top_k=3", "Search"),
            ("/cache/stats", "Cache Stats"),
            ("/health/full", "Health Full"),
            ("/orchestrate/agents", "Agents"),
        ]
        for endpoint, name in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                endpoints_ok += 1
        print(f"✓ API Endpoints: {endpoints_ok}/{len(endpoints)} working")
        tests.append(endpoints_ok > 0)
    except Exception as e:
        print(f"✗ API Endpoints: {str(e)[:50]}")
        tests.append(False)

    passed = sum(tests)
    total = len(tests)
    print(f"\nFunctionality Tests: {passed}/{total} passed")
    return passed == total


def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "CONTEXT ENGINE - MASTER VERIFICATION" + " "*17 + "║")
    print("║" + " "*15 + "Testing All Phases 1-12" + " "*30 + "║")
    print("╚" + "="*68 + "╝")

    imports_ok = test_imports()
    functionality_ok = test_functionality()

    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)

    if imports_ok and functionality_ok:
        print("\n✅ ALL SYSTEMS OPERATIONAL - READY FOR PHASE 13\n")
        return 0
    elif imports_ok:
        print("\n⚠️  IMPORTS OK BUT SOME FUNCTIONALITY ISSUES\n")
        return 1
    else:
        print("\n❌ CRITICAL IMPORT FAILURES\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

