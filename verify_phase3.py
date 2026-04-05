from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("PHASE 3 VERIFICATION")
print("=" * 80)

results = {}

print("\n[TEST 1] Ollama Agent...")
try:
    from src.agent.ollama_agent import query_agent
    result = query_agent("why is login failing", ".")
    assert "task" in result
    assert "answer" in result
    assert "context_used" in result
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0
    assert result["context_used"]["chunks"] >= 1
    print(f"✓ PASS: Agent returned answer")
    print(f"  Answer preview: {result['answer'][:200]}...")
    results["Agent"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Agent"] = False

print("\n[TEST 2] Watcher Import...")
try:
    from src.agent.watcher import start_watcher
    print(f"✓ PASS: Watcher module loaded")
    results["Watcher"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Watcher"] = False

print("\n[TEST 3] API /ask Endpoint...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/ask?task=why+is+login+failing")
    assert response.status_code == 200, f"Got status {response.status_code}"
    data = response.json()
    assert "answer" in data
    print(f"✓ PASS: /ask endpoint works")
    print(f"  Answer preview: {data['answer'][:100]}...")
    results["API /ask"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API /ask"] = False

print("\n[TEST 4] API /watch Endpoint...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.post("/watch", json={"directory": "test-codebase"})
    assert response.status_code == 200, f"Got status {response.status_code}"
    data = response.json()
    assert "status" in data
    assert data["status"] in ["watching", "already_watching"]
    print(f"✓ PASS: /watch endpoint works")
    print(f"  Response: {data}")
    results["API /watch"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API /watch"] = False

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
    print("\n🎉 Phase 3 complete. Ready for Phase 4.")
    sys.exit(0)
else:
    failed = [name for name, p in results.items() if not p]
    print(f"\n⚠️ {total - passed} test(s) failed: {', '.join(failed)}")
    sys.exit(1)

