from __future__ import annotations
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("PHASE 6 VERIFICATION")
print("=" * 80)

results = {}

print("\n[TEST 1] Extension files exist...")
try:
    ext_dir = Path("vscode-extension")
    assert (ext_dir / "package.json").exists(), "package.json not found"
    assert (ext_dir / "extension.js").exists(), "extension.js not found"
    assert (ext_dir / "media" / "panel.html").exists(), "media/panel.html not found"
    print("✓ PASS: All 3 files exist")
    results["Files Exist"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Files Exist"] = False

print("\n[TEST 2] package.json is valid...")
try:
    with open("vscode-extension/package.json", "r") as f:
        pkg = json.load(f)
    assert pkg.get("name") == "context-engine", "name mismatch"
    assert pkg.get("main") == "./extension.js", "main mismatch"
    assert "contextEngine.openPanel" in [c.get("command") for c in pkg.get("contributes", {}).get("commands", [])], "command not found"
    print(f"✓ PASS: package.json valid")
    print(f"  Name: {pkg.get('name')}, Version: {pkg.get('version')}")
    results["package.json"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["package.json"] = False

print("\n[TEST 3] extension.js structure...")
try:
    with open("vscode-extension/extension.js", "r") as f:
        content = f.read()
    assert "contextEngine.openPanel" in content, "openPanel command not found"
    assert "createWebviewPanel" in content or "WebviewPanel" in content, "WebviewPanel not found"
    assert "onDidReceiveMessage" in content, "message handler not found"
    assert "localhost:8000" in content, "backend URL not found"
    print("✓ PASS: extension.js structure OK")
    results["extension.js"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["extension.js"] = False

print("\n[TEST 4] panel.html structure...")
try:
    with open("vscode-extension/media/panel.html", "r") as f:
        content = f.read()
    assert "acquireVsCodeApi" in content, "acquireVsCodeApi not found"
    assert "Ask AI" in content, "Ask AI tab not found"
    assert "Search" in content, "Search tab not found"
    assert "Health" in content, "Health tab not found"
    assert "Graph" in content, "Graph tab not found"
    assert "localhost:8000" not in content, "panel.html should NOT call backend directly"
    print("✓ PASS: panel.html structure OK")
    results["panel.html"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["panel.html"] = False

print("\n[TEST 5] Backend /health works...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200, f"Status {response.status_code}"
    assert response.json() == {"status": "ok"}
    print("✓ PASS: Backend healthy")
    results["Backend Health"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Backend Health"] = False

print("\n[TEST 6] Backend /report endpoint...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/report?task=what+does+login+do")
    assert response.status_code == 200, f"Status {response.status_code}"
    data = response.json()
    assert "report" in data, "report key missing"
    print(f"✓ PASS: /report works")
    print(f"  Report length: {len(data['report'])} chars")
    results["API /report"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API /report"] = False

print("\n[TEST 7] Backend /cli-help endpoint...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/cli-help")
    assert response.status_code == 200
    data = response.json()
    assert "commands" in data, "commands missing"
    assert len(data["commands"]) >= 8, "not enough commands"
    print(f"✓ PASS: /cli-help works")
    print(f"  Commands: {len(data['commands'])}")
    results["API /cli-help"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API /cli-help"] = False

print("\n[TEST 8] panel.html has all 4 tabs...")
try:
    with open("vscode-extension/media/panel.html", "r") as f:
        content = f.read()
    tabs = ["Ask AI", "Search", "Health", "Graph"]
    for tab in tabs:
        assert tab in content, f"Tab '{tab}' not found"
    print("✓ PASS: All 4 tabs present")
    print(f"  Tabs: {', '.join(tabs)}")
    results["Tabs"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Tabs"] = False

print("\n[TEST 9] extension.js handles all message types...")
try:
    with open("vscode-extension/extension.js", "r") as f:
        content = f.read()
    types = ["ask", "search", "health", "index", "deps", "report"]
    for msg_type in types:
        assert f'type === "{msg_type}"' in content or f"== '{msg_type}'" in content, f"Type '{msg_type}' not handled"
    print("✓ PASS: All message types handled")
    print(f"  Types: {', '.join(types)}")
    results["Message Types"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Message Types"] = False

print("\n[TEST 10] panel.html has no hardcoded localhost...")
try:
    with open("vscode-extension/media/panel.html", "r") as f:
        content = f.read()
    assert "localhost" not in content, "panel.html should NOT contain localhost"
    print("✓ PASS: Panel correctly delegates to extension.js")
    results["Panel Delegation"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Panel Delegation"] = False

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
    print("\n🎉 Phase 6 complete. Ready for Phase 7.")
    sys.exit(0)
else:
    failed = [name for name, p in results.items() if not p]
    print(f"\n⚠️ {total - passed} test(s) failed: {', '.join(failed)}")
    sys.exit(1)

