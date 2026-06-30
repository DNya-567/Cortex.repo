from __future__ import annotations
import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("PHASE 9 VERIFICATION")
print("=" * 80)

results = {}

print("\n[TEST 1] generate_api_key...")
try:
    from src.auth.api_keys import generate_api_key
    result = generate_api_key("test-app")
    assert "key" in result, "Missing key"
    assert result["key"].startswith("ce-"), "Key prefix wrong"
    assert len(result["key"]) == 35, f"Key length wrong: {len(result['key'])}"
    assert "prefix" in result, "Missing prefix"
    print(f"✓ PASS: Generated key with prefix {result['prefix']}")
    results["Generate Key"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Generate Key"] = False

print("\n[TEST 2] verify_api_key valid...")
try:
    from src.auth.api_keys import generate_api_key, verify_api_key
    result = generate_api_key("test-app-2")
    key = result["key"]
    is_valid = verify_api_key(key)
    assert is_valid == True, f"Key should be valid"
    print("✓ PASS: Valid key verified")
    results["Verify Valid"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Verify Valid"] = False

print("\n[TEST 3] verify_api_key invalid...")
try:
    from src.auth.api_keys import verify_api_key
    is_valid = verify_api_key("ce-invalidkeyxxxxxxxxxxxxxxxxxxxxxxxx")
    assert is_valid == False, "Invalid key should fail"
    print("✓ PASS: Invalid key rejected")
    results["Verify Invalid"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Verify Invalid"] = False

print("\n[TEST 4] list_api_keys...")
try:
    from src.auth.api_keys import list_api_keys
    keys = list_api_keys()
    assert isinstance(keys, list), "Should return list"
    assert len(keys) >= 1, "Should have at least 1 key"
    assert "prefix" in keys[0], "Missing prefix in key"
    assert "key" not in keys[0], "Raw key should not be returned"
    print(f"✓ PASS: Listed {len(keys)} key(s)")
    results["List Keys"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["List Keys"] = False

print("\n[TEST 5] revoke_api_key...")
try:
    from src.auth.api_keys import generate_api_key, revoke_api_key, verify_api_key
    result = generate_api_key("test-revoke")
    key = result["key"]
    prefix = result["prefix"]

    success = revoke_api_key(prefix)
    assert success == True, "Revocation should succeed"

    is_valid = verify_api_key(key)
    assert is_valid == False, "Revoked key should be invalid"
    print("✓ PASS: Key revoked successfully")
    results["Revoke Key"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Revoke Key"] = False

print("\n[TEST 6] rate limiter...")
try:
    from src.auth.rate_limiter import check_rate_limit, get_rate_limit_status
    for _ in range(5):
        result = check_rate_limit("ce-test12")
        assert result == True, "Should be under limit"

    status = get_rate_limit_status("ce-test12")
    assert status["requests_this_window"] == 5, f"Expected 5 requests, got {status['requests_this_window']}"
    print(f"✓ PASS: Rate limiter working - {status}")
    results["Rate Limiter"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Rate Limiter"] = False

print("\n[TEST 7] API POST /auth/keys...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.post("/auth/keys", json={"name": "api-test"})
    assert response.status_code == 200, f"Status {response.status_code}"
    data = response.json()
    assert "key" in data, "Missing key"
    assert data["key"].startswith("ce-"), "Wrong prefix"
    print("✓ PASS: API key generation endpoint works")
    results["API Generate"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API Generate"] = False

print("\n[TEST 8] API GET /auth/keys...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/auth/keys")
    assert response.status_code == 200, f"Status {response.status_code}"
    data = response.json()
    assert "keys" in data, "Missing keys"
    print(f"✓ PASS: Listed {len(data['keys'])} keys")
    results["API List"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API List"] = False

print("\n[TEST 9] API DELETE /auth/keys/{prefix}...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)

    # Generate key via API
    response = client.post("/auth/keys", json={"name": "delete-test"})
    key_data = response.json()
    prefix = key_data["prefix"]

    # Delete it
    response = client.delete(f"/auth/keys/{prefix}")
    assert response.status_code == 200, f"Status {response.status_code}"
    data = response.json()
    assert data["status"] == "revoked", f"Wrong status: {data['status']}"
    print("✓ PASS: Revocation endpoint works")
    results["API Revoke"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API Revoke"] = False

print("\n[TEST 10] Auth middleware disabled...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)

    # AUTH_ENABLED should be false, so request without key should work
    response = client.get("/search?query=login")
    assert response.status_code == 200, f"Status {response.status_code} (auth should be disabled)"
    print("✓ PASS: Auth middleware correctly disabled")
    results["Auth Disabled"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Auth Disabled"] = False

print("\n[TEST 11] CLI key-generate command...")
try:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.cli", "key-generate", "test-cli-app"],
        cwd=str(Path(__file__).parent),
        capture_output=True,
        text=True,
        env=env,
        timeout=30
    )
    assert result.returncode == 0, f"Exit code {result.returncode}"
    output = result.stdout + result.stderr
    assert "ce-" in output, "No key in output"
    assert "IMPORTANT" in output, "No warning in output"
    print("✓ PASS: CLI key-generate works")
    lines = output.split("\n")
    for line in lines[:3]:
        if line.strip():
            print(f"  {line}")
    results["CLI Generate"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["CLI Generate"] = False

print("\n[TEST 12] CLI key-list command...")
try:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.cli", "key-list"],
        cwd=str(Path(__file__).parent),
        capture_output=True,
        text=True,
        env=env,
        timeout=30
    )
    assert result.returncode == 0, f"Exit code {result.returncode}"
    output = result.stdout + result.stderr
    assert len(output) > 0, "No output"
    print("✓ PASS: CLI key-list works")
    print(f"  Output: {output.split(chr(10))[0]}")
    results["CLI List"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["CLI List"] = False

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
    print("\n🎉 Phase 9 complete. Ready for Phase 10.")
    sys.exit(0)
else:
    failed = [name for name, p in results.items() if not p]
    print(f"\n⚠️ {total - passed} test(s) failed: {', '.join(failed)}")
    sys.exit(1)

