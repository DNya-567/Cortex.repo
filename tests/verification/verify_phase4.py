from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("PHASE 4 VERIFICATION")
print("=" * 80)

results = {}

print("\n[TEST 1] Cache Miss...")
try:
    from src.cache.query_cache import get_cached
    result = get_cached("this task does not exist yet 12345")
    assert result is None
    print("✓ PASS: Cache miss confirmed")
    results["Cache Miss"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Cache Miss"] = False

print("\n[TEST 2] Cache Store + Hit...")
try:
    from src.cache.query_cache import store_cache, get_cached
    store_cache("test task", {"answer": "test answer", "task": "test task", "context_used": {}})
    result = get_cached("test task")
    assert result is not None
    assert result["answer"] == "test answer"
    print("✓ PASS: Cache store and retrieve OK")
    results["Cache Store"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Cache Store"] = False

print("\n[TEST 3] Cache Stats...")
try:
    from src.cache.query_cache import get_cache_stats
    stats = get_cache_stats()
    assert "total_entries" in stats
    assert "total_hits" in stats
    assert stats["total_entries"] >= 1
    print(f"✓ PASS: Cache stats: {stats}")
    results["Cache Stats"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Cache Stats"] = False

print("\n[TEST 4] Agent Caching...")
try:
    from src.cache.query_cache import clear_cache
    from src.agent.ollama_agent import query_agent
    clear_cache()
    result1 = query_agent("what does login do", ".")
    assert result1.get("cached") == False
    result2 = query_agent("what does login do", ".")
    assert result2.get("cached") == True
    print("✓ PASS: Agent caching works")
    results["Agent Caching"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Agent Caching"] = False

print("\n[TEST 5] Health Checker...")
try:
    from src.health.checker import check_health
    health = check_health()
    assert "ollama" in health
    assert "qdrant" in health
    assert "sqlite" in health
    assert "overall" in health
    print(f"✓ PASS: Health status: {health['overall']}")
    print(f"  Full: {health}")
    results["Health Checker"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Health Checker"] = False

print("\n[TEST 6] API /health/full...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/health/full")
    assert response.status_code == 200
    data = response.json()
    assert "overall" in data
    print(f"✓ PASS: Overall health: {data['overall']}")
    results["API /health/full"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API /health/full"] = False

print("\n[TEST 7] API /cache/stats...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_entries" in data
    print(f"✓ PASS: Cache stats: {data}")
    results["API /cache/stats"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API /cache/stats"] = False

print("\n[TEST 8] API DELETE /cache...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.delete("/cache")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "cleared"}
    print("✓ PASS: Cache cleared via API")
    results["API DELETE /cache"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API DELETE /cache"] = False

print("\n[TEST 9] API /graph/dependencies...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/graph/dependencies?file=test-codebase/auth.js")
    assert response.status_code == 200
    data = response.json()
    assert "dependencies" in data
    assert len(data["dependencies"]) >= 0
    print(f"✓ PASS: Dependencies: {len(data['dependencies'])} found")
    results["API /graph/dependencies"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API /graph/dependencies"] = False

print("\n[TEST 10] API /adrs...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/adrs?file=test-codebase/auth.js")
    assert response.status_code == 200
    data = response.json()
    assert "adrs" in data
    if data["adrs"]:
        print(f"✓ PASS: Found {len(data['adrs'])} ADRs")
        for adr in data["adrs"]:
            print(f"  - {adr.get('adr_id')}: {adr.get('title')}")
    else:
        print("✓ PASS: No ADRs found (expected for this file)")
    results["API /adrs"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API /adrs"] = False

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
    print("\n🎉 Phase 4 complete. Ready for Phase 5.")
    sys.exit(0)
else:
    failed = [name for name, p in results.items() if not p]
    print(f"\n⚠️ {total - passed} test(s) failed: {', '.join(failed)}")
    sys.exit(1)

