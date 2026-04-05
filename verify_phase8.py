from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("PHASE 8 VERIFICATION")
print("=" * 80)

results = {}

print("\n[TEST 1] streaming_agent import...")
try:
    from src.agent.streaming_agent import stream_agent
    print("✓ PASS: streaming_agent imported OK")
    results["Import"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Import"] = False

print("\n[TEST 2] stream_agent yields tokens...")
try:
    from src.agent.streaming_agent import stream_agent
    tokens = list(stream_agent("what does login do", "."))
    assert len(tokens) > 0, f"No tokens returned, got {len(tokens)}"
    assert all(isinstance(t, str) for t in tokens), "Not all tokens are strings"
    joined = "".join(tokens)
    assert len(joined) > 20, f"Response too short: {len(joined)} chars"
    print(f"✓ PASS: Got {len(tokens)} tokens")
    print(f"  Response preview: {joined[:100]}...")
    results["Streaming"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Streaming"] = False

print("\n[TEST 3] stream coherence...")
try:
    from src.agent.streaming_agent import stream_agent
    tokens = list(stream_agent("what does login do", "."))
    joined = "".join(tokens)
    assert len(joined) > 50, f"Response too short: {len(joined)} chars"
    assert "[DONE]" not in joined, "[DONE] should not be in agent response"
    print("✓ PASS: Stream coherence OK")
    results["Coherence"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Coherence"] = False

print("\n[TEST 4] API /stream endpoint exists...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/stream?task=what+does+login+do")
    assert response.status_code == 200, f"Status {response.status_code}"
    assert "text/event-stream" in response.headers.get("content-type", ""), "Wrong content type"
    print("✓ PASS: SSE endpoint reachable")
    results["Endpoint"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Endpoint"] = False

print("\n[TEST 5] API /stream response format...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/stream?task=what+does+login+do")
    text = response.text
    assert "data:" in text, "No SSE data: prefix"
    assert "[DONE]" in text, "No [DONE] marker"
    print("✓ PASS: SSE format correct")
    print(f"  Response preview: {text[:200]}...")
    results["Format"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Format"] = False

print("\n[TEST 6] API /stream empty task...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/stream?task=")
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    print("✓ PASS: Empty task rejected correctly")
    results["Validation"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Validation"] = False

print("\n[TEST 7] API /ask still works...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/ask?task=what+does+login+do")
    assert response.status_code == 200, f"Status {response.status_code}"
    data = response.json()
    assert "answer" in data, "Missing answer key"
    print("✓ PASS: Non-streaming /ask still works")
    results["Non-Streaming"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Non-Streaming"] = False

print("\n[TEST 8] API /health still works...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("✓ PASS: Health check OK")
    results["Health"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Health"] = False

print("\n[TEST 9] panel.html has streaming UI...")
try:
    with open("vscode-extension/media/panel.html", "r") as f:
        content = f.read()
    assert "EventSource" in content, "No EventSource"
    assert "stream" in content.lower(), "No streaming mention"
    assert "[DONE]" in content, "No [DONE] marker"
    print("✓ PASS: panel.html streaming UI OK")
    results["Panel UI"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Panel UI"] = False

print("\n[TEST 10] panel.html has stream toggle...")
try:
    with open("vscode-extension/media/panel.html", "r") as f:
        content = f.read()
    assert 'type="checkbox"' in content or "checkbox" in content, "No checkbox"
    assert "Stream" in content, "No Stream toggle label"
    print("✓ PASS: Stream toggle found in panel.html")
    results["Toggle"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Toggle"] = False

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
    print("\n🎉 Phase 8 complete. Ready for Phase 9.")
    sys.exit(0)
else:
    failed = [name for name, p in results.items() if not p]
    print(f"\n⚠️ {total - passed} test(s) failed: {', '.join(failed)}")
    sys.exit(1)

