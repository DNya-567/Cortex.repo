from __future__ import annotations
import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("PHASE 10 VERIFICATION - FINAL POLISH + DEPLOYMENT")
print("=" * 80)

results = {}

print("\n[TEST 1] README.md exists and has required sections...")
try:
    with open("README.md", "r") as f:
        content = f.read()

    required = ["Context Engine", "Architecture", "Tech Stack", "Quick Start",
                "API Endpoints", "CLI Commands", "Prerequisites", "Phase Completion"]

    for section in required:
        assert section in content, f"Missing section: {section}"

    print(f"✓ PASS: All {len(required)} sections found")
    results["README"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["README"] = False

print("\n[TEST 2] .env.example has all required keys...")
try:
    with open(".env.example", "r") as f:
        content = f.read()

    required_keys = ["OLLAMA_URL", "QDRANT_URL", "COLLECTION_NAME",
                     "EMBED_MODEL", "OLLAMA_CHAT_MODEL", "AUTH_ENABLED"]

    for key in required_keys:
        assert key in content, f"Missing key: {key}"

    print(f"✓ PASS: All {len(required_keys)} env keys documented")
    results[".env.example"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results[".env.example"] = False

print("\n[TEST 3] requirements.txt has all packages...")
try:
    with open("requirements.txt", "r") as f:
        content = f.read()

    required_packages = ["fastapi", "uvicorn", "qdrant-client", "httpx",
                        "python-dotenv", "watchdog", "tree-sitter", "gitpython",
                        "sentence-transformers"]

    for pkg in required_packages:
        assert pkg in content, f"Missing package: {pkg}"

    print(f"✓ PASS: All {len(required_packages)} packages documented")
    results["requirements.txt"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["requirements.txt"] = False

print("\n[TEST 4] Dockerfile exists and is valid...")
try:
    with open("Dockerfile", "r") as f:
        content = f.read()

    required = ["FROM python:3.13", "WORKDIR /app", "requirements.txt",
                "EXPOSE 8000", "uvicorn src.api.main:app"]

    for item in required:
        assert item in content, f"Missing item: {item}"

    print("✓ PASS: Dockerfile valid")
    results["Dockerfile"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Dockerfile"] = False

print("\n[TEST 5] docker-compose.yml exists and is valid...")
try:
    with open("docker-compose.yml", "r") as f:
        content = f.read()

    required = ["qdrant", "ollama", "context-engine", "8000", "6333", "11434"]

    for item in required:
        assert item in content, f"Missing item: {item}"

    print("✓ PASS: docker-compose.yml valid")
    results["docker-compose.yml"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["docker-compose.yml"] = False

print("\n[TEST 6] Full API health check...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    response = client.get("/health/full")
    assert response.status_code == 200
    assert "overall" in response.json()

    print("✓ PASS: API health checks work")
    results["API Health"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API Health"] = False

print("\n[TEST 7] Full pipeline smoke test...")
try:
    from src.indexer import index_directory
    from src.search.searcher import search

    result = index_directory("test-codebase")
    assert result["status"] == "ok", f"Index failed: {result}"
    assert result["total_chunks"] >= 3, f"Not enough chunks: {result['total_chunks']}"

    results_list = search("login", top_k=1)
    assert len(results_list) >= 1, "No search results"
    assert results_list[0]["chunk_name"] == "login", f"Wrong chunk: {results_list[0]['chunk_name']}"

    print("✓ PASS: Full pipeline works")
    results["Pipeline"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Pipeline"] = False

print("\n[TEST 8] All src/ subpackages importable...")
try:
    modules = [
        "src.chunker.chunker",
        "src.embedder.embedder",
        "src.storage.qdrant_store",
        "src.search.searcher",
        "src.indexer",
        "src.graph.import_resolver",
        "src.context.adr_store",
        "src.context.git_log",
        "src.context.context_pack",
        "src.agent.ollama_agent",
        "src.agent.streaming_agent",
        "src.agent.watcher",
        "src.health.checker",
        "src.cache.query_cache",
        "src.reporter.report",
        "src.cli.cli",
        "src.auth.api_keys",
        "src.auth.middleware",
        "src.auth.rate_limiter",
    ]

    for mod in modules:
        __import__(mod)

    print(f"✓ PASS: All {len(modules)}/19 modules importable")
    results["Modules"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Modules"] = False

print("\n[TEST 9] CLI smoke test...")
try:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."

    result = subprocess.run(
        [sys.executable, "-m", "src.cli.cli", "health"],
        cwd=str(Path(__file__).parent),
        capture_output=True,
        text=True,
        env=env,
        timeout=30
    )
    assert result.returncode == 0, f"Exit code {result.returncode}"

    result = subprocess.run(
        [sys.executable, "-m", "src.cli.cli", "cache-stats"],
        cwd=str(Path(__file__).parent),
        capture_output=True,
        text=True,
        env=env,
        timeout=30
    )
    assert result.returncode == 0, f"Exit code {result.returncode}"

    print("✓ PASS: CLI smoke test passed")
    results["CLI"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["CLI"] = False

print("\n[TEST 10] Project structure complete...")
try:
    required_files = [
        "src/chunker/chunker.py",
        "src/chunker/python_chunker.py",
        "src/chunker/generic_chunker.py",
        "src/chunker/chunk_stats.py",
        "src/embedder/embedder.py",
        "src/storage/qdrant_store.py",
        "src/search/searcher.py",
        "src/indexer.py",
        "src/graph/import_resolver.py",
        "src/context/adr_store.py",
        "src/context/git_log.py",
        "src/context/context_pack.py",
        "src/agent/ollama_agent.py",
        "src/agent/streaming_agent.py",
        "src/agent/watcher.py",
        "src/health/checker.py",
        "src/cache/query_cache.py",
        "src/reporter/report.py",
        "src/cli/cli.py",
        "src/auth/api_keys.py",
        "src/auth/middleware.py",
        "src/auth/rate_limiter.py",
        "src/api/main.py",
        "vscode-extension/extension.js",
        "vscode-extension/media/panel.html",
        "README.md",
        ".env.example",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
    ]

    missing = []
    for f in required_files:
        if not Path(f).exists():
            missing.append(f)

    assert not missing, f"Missing files: {missing}"

    print(f"✓ PASS: All {len(required_files)}/30 files present")
    results["Structure"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Structure"] = False

print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

passed = sum(1 for v in results.values() if v)
total = len(results)

for test_name, passed_flag in results.items():
    status = "✓ PASS" if passed_flag else "✗ FAIL"
    print(f"{status}: {test_name}")

print(f"\nTotal: {passed}/{total} tests passed")

if passed == total:
    print("\n" + "=" * 80)
    print("  CONTEXT ENGINE — ALL 10 PHASES COMPLETE  🎉")
    print("  Ready for production deployment.")
    print("=" * 80)
    sys.exit(0)
else:
    failed = [name for name, p in results.items() if not p]
    print(f"\n⚠️ {total - passed} test(s) failed: {', '.join(failed)}")
    sys.exit(1)

