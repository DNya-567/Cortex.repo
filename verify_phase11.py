#!/usr/bin/env python3
"""
Phase 11 Verification Script — GitHub Integration + File Tree Explorer
Test GitHub API client, repo browsing, PR reading, and indexing.
"""

import sys
import os
import subprocess
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
os.environ["PYTHONPATH"] = "."


def test_1_github_client_import():
    """TEST 1: GitHub client import."""
    print("\n[TEST 1] GitHub client import")
    try:
        from src.github.github_client import gh_get, gh_get_raw
        print("  [OK] GitHub client imported OK")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_2_repo_info():
    """TEST 2: get_repo_info (public repo)."""
    print("\n[TEST 2] get_repo_info (public repo)")
    try:
        from src.github.repo import get_repo_info
        result = get_repo_info("octocat", "Hello-World")

        if "name" not in result:
            print("  [FAIL] FAILED: 'name' not in result")
            return False
        if result["name"] != "Hello-World":
            print("  [FAIL] FAILED: repo name mismatch")
            return False

        print(f"  [OK] Repo: {result.get('full_name', '')}")
        print(f"    Description: {result.get('description', '')[:60]}")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_3_file_tree():
    """TEST 3: get_file_tree."""
    print("\n[TEST 3] get_file_tree")
    try:
        from src.github.repo import get_file_tree
        result = get_file_tree("octocat", "Hello-World")

        if not isinstance(result, list):
            print("  [FAIL] FAILED: result is not a list")
            return False
        if len(result) < 1:
            print("  [FAIL] FAILED: empty result")
            return False
        if "name" not in result[0]:
            print("  [FAIL] FAILED: 'name' not in first item")
            return False
        if "type" not in result[0]:
            print("  [FAIL] FAILED: 'type' not in first item")
            return False

        print(f"  [OK] Found {len(result)} items in tree")
        for i, item in enumerate(result[:3]):
            print(f"    {item['type']:<4} {item['name']}")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_4_file_tree_recursive():
    """TEST 4: get_file_tree_recursive."""
    print("\n[TEST 4] get_file_tree_recursive")
    try:
        from src.github.repo import get_file_tree_recursive
        result = get_file_tree_recursive("octocat", "Hello-World", max_depth=2)

        if not isinstance(result, list):
            print("  [FAIL] FAILED: result is not a list")
            return False
        if not all("depth" in item for item in result):
            print("  [FAIL] FAILED: not all items have 'depth' key")
            return False

        print(f"  [OK] Found {len(result)} items (recursive)")
        depths = set(item.get("depth") for item in result)
        print(f"    Depths: {sorted(depths)}")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_5_file_content():
    """TEST 5: get_file_content."""
    print("\n[TEST 5] get_file_content")
    try:
        from src.github.repo import get_file_content
        result = get_file_content("octocat", "Hello-World", "README")

        if "content" not in result:
            print("  [FAIL] FAILED: 'content' not in result")
            return False
        if "lines" not in result:
            print("  [FAIL] FAILED: 'lines' not in result")
            return False
        if len(result["content"]) == 0:
            print("  [FAIL] FAILED: empty content")
            return False

        print(f"  [OK] File: {result.get('path', '')}")
        print(f"    Lines: {result.get('lines', 0)}")
        print(f"    Language: {result.get('language', '')}")
        print(f"    Content preview: {result['content'][:100]}")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_6_pull_requests():
    """TEST 6: list_pull_requests."""
    print("\n[TEST 6] list_pull_requests")
    try:
        from src.github.pr_reader import list_pull_requests
        result = list_pull_requests("octocat", "Hello-World", state="all", limit=5)

        if not isinstance(result, list):
            print("  [FAIL] FAILED: result is not a list")
            return False

        print(f"  [OK] Found {len(result)} PRs")
        if result:
            for pr in result[:2]:
                print(f"    #{pr.get('number', 0)}: {pr.get('title', '')}")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_7_api_github_repo():
    """TEST 7: API /github/repo endpoint."""
    print("\n[TEST 7] API /github/repo endpoint")
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/github/repo?owner=octocat&repo=Hello-World")

        if response.status_code != 200:
            print(f"  [FAIL] FAILED: status {response.status_code}")
            return False

        data = response.json()
        if "name" not in data:
            print("  [FAIL] FAILED: 'name' not in response")
            return False

        print(f"  [OK] Endpoint works")
        print(f"    Repo: {data.get('name', '')}")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_8_api_github_tree():
    """TEST 8: API /github/tree endpoint."""
    print("\n[TEST 8] API /github/tree endpoint")
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/github/tree?owner=octocat&repo=Hello-World")

        if response.status_code != 200:
            print(f"  [FAIL] FAILED: status {response.status_code}")
            return False

        data = response.json()
        if "tree" not in data:
            print("  [FAIL] FAILED: 'tree' not in response")
            return False

        tree = data["tree"]
        print(f"  [OK] Endpoint works")
        print(f"    Found {len(tree)} items")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_9_module_files_exist():
    """TEST 9: GitHub module files exist."""
    print("\n[TEST 9] GitHub module files exist")
    try:
        required_files = [
            "src/github/__init__.py",
            "src/github/github_client.py",
            "src/github/repo.py",
            "src/github/indexer.py",
            "src/github/pr_reader.py",
        ]

        project_root = Path(__file__).parent
        all_exist = True

        for file_path in required_files:
            full_path = project_root / file_path
            if full_path.exists():
                print(f"  [OK] {file_path}")
            else:
                print(f"  [FAIL] {file_path} MISSING")
                all_exist = False

        if all_exist:
            print("  [OK] All GitHub module files present")
            return True
        else:
            return False
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_10_cli_gh_tree_command():
    """TEST 10: CLI gh-tree command."""
    print("\n[TEST 10] CLI gh-tree command")
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = "."

        result = subprocess.run(
            [sys.executable, "-m", "src.cli.cli", "gh-tree", "octocat", "Hello-World"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent,
            env=env
        )

        if result.returncode != 0:
            print(f"  [FAIL] FAILED: exit code {result.returncode}")
            print(f"    stderr: {result.stderr[:200]}")
            return False

        stdout = result.stdout
        if not stdout:
            print("  [FAIL] FAILED: empty output")
            return False

        print(f"  [OK] CLI command works")
        lines = stdout.split('\n')[:3]
        for line in lines:
            if line.strip():
                print(f"    {line}")
        return True
    except subprocess.TimeoutExpired:
        print("  [FAIL] FAILED: timeout")
        return False
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("PHASE 11 - GITHUB INTEGRATION + FILE TREE EXPLORER")
    print("=" * 70)

    tests = [
        test_1_github_client_import,
        test_2_repo_info,
        test_3_file_tree,
        test_4_file_tree_recursive,
        test_5_file_content,
        test_6_pull_requests,
        test_7_api_github_repo,
        test_8_api_github_tree,
        test_9_module_files_exist,
        test_10_cli_gh_tree_command,
    ]

    results = [test() for test in tests]
    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{total} passed")
    print("=" * 70)

    if passed == total:
        print("\n[OK] Phase 11 complete. Ready for Phase 12.")
        return 0
    else:
        failed = [i + 1 for i, r in enumerate(results) if not r]
        print(f"\n[FAIL] Failed tests: {', '.join(map(str, failed))}")
        return 1


if __name__ == "__main__":
    sys.exit(main())


def test_2_repo_info():
    """TEST 2: get_repo_info (public repo)."""
    print("\n[TEST 2] get_repo_info (public repo)")
    try:
        from src.github.repo import get_repo_info
        result = get_repo_info("octocat", "Hello-World")

        if "name" not in result:
            print("  ✗ FAILED: 'name' not in result")
            return False
        if result["name"] != "Hello-World":
            print("  ✗ FAILED: repo name mismatch")
            return False

        print(f"  ✓ Repo: {result.get('full_name', '')}")
        print(f"    Description: {result.get('description', '')[:60]}")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_3_file_tree():
    """TEST 3: get_file_tree."""
    print("\n[TEST 3] get_file_tree")
    try:
        from src.github.repo import get_file_tree
        result = get_file_tree("octocat", "Hello-World")

        if not isinstance(result, list):
            print("  ✗ FAILED: result is not a list")
            return False
        if len(result) < 1:
            print("  ✗ FAILED: empty result")
            return False
        if "name" not in result[0]:
            print("  ✗ FAILED: 'name' not in first item")
            return False
        if "type" not in result[0]:
            print("  ✗ FAILED: 'type' not in first item")
            return False

        print(f"  ✓ Found {len(result)} items in tree")
        for i, item in enumerate(result[:3]):
            print(f"    {item['type']:<4} {item['name']}")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_4_file_tree_recursive():
    """TEST 4: get_file_tree_recursive."""
    print("\n[TEST 4] get_file_tree_recursive")
    try:
        from src.github.repo import get_file_tree_recursive
        result = get_file_tree_recursive("octocat", "Hello-World", max_depth=2)

        if not isinstance(result, list):
            print("  ✗ FAILED: result is not a list")
            return False
        if not all("depth" in item for item in result):
            print("  ✗ FAILED: not all items have 'depth' key")
            return False

        print(f"  ✓ Found {len(result)} items (recursive)")
        depths = set(item.get("depth") for item in result)
        print(f"    Depths: {sorted(depths)}")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_5_file_content():
    """TEST 5: get_file_content."""
    print("\n[TEST 5] get_file_content")
    try:
        from src.github.repo import get_file_content
        result = get_file_content("octocat", "Hello-World", "README")

        if "content" not in result:
            print("  ✗ FAILED: 'content' not in result")
            return False
        if "lines" not in result:
            print("  ✗ FAILED: 'lines' not in result")
            return False
        if len(result["content"]) == 0:
            print("  ✗ FAILED: empty content")
            return False

        print(f"  ✓ File: {result.get('path', '')}")
        print(f"    Lines: {result.get('lines', 0)}")
        print(f"    Language: {result.get('language', '')}")
        print(f"    Content preview: {result['content'][:100]}")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_6_pull_requests():
    """TEST 6: list_pull_requests."""
    print("\n[TEST 6] list_pull_requests")
    try:
        from src.github.pr_reader import list_pull_requests
        result = list_pull_requests("octocat", "Hello-World", state="all", limit=5)

        if not isinstance(result, list):
            print("  ✗ FAILED: result is not a list")
            return False

        print(f"  ✓ Found {len(result)} PRs")
        if result:
            for pr in result[:2]:
                print(f"    #{pr.get('number', 0)}: {pr.get('title', '')}")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_7_api_github_repo():
    """TEST 7: API /github/repo endpoint."""
    print("\n[TEST 7] API /github/repo endpoint")
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/github/repo?owner=octocat&repo=Hello-World")

        if response.status_code != 200:
            print(f"  ✗ FAILED: status {response.status_code}")
            return False

        data = response.json()
        if "name" not in data:
            print("  ✗ FAILED: 'name' not in response")
            return False

        print(f"  ✓ Endpoint works")
        print(f"    Repo: {data.get('name', '')}")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_8_api_github_tree():
    """TEST 8: API /github/tree endpoint."""
    print("\n[TEST 8] API /github/tree endpoint")
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app

        client = TestClient(app)
        response = client.get("/github/tree?owner=octocat&repo=Hello-World")

        if response.status_code != 200:
            print(f"  ✗ FAILED: status {response.status_code}")
            return False

        data = response.json()
        if "tree" not in data:
            print("  ✗ FAILED: 'tree' not in response")
            return False

        tree = data["tree"]
        print(f"  ✓ Endpoint works")
        print(f"    Found {len(tree)} items")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_9_module_files_exist():
    """TEST 9: GitHub module files exist."""
    print("\n[TEST 9] GitHub module files exist")
    try:
        required_files = [
            "src/github/__init__.py",
            "src/github/github_client.py",
            "src/github/repo.py",
            "src/github/indexer.py",
            "src/github/pr_reader.py",
        ]

        project_root = Path(__file__).parent
        all_exist = True

        for file_path in required_files:
            full_path = project_root / file_path
            if full_path.exists():
                print(f"  ✓ {file_path}")
            else:
                print(f"  ✗ {file_path} MISSING")
                all_exist = False

        if all_exist:
            print("  ✓ All GitHub module files present")
            return True
        else:
            return False
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_10_cli_gh_tree_command():
    """TEST 10: CLI gh-tree command."""
    print("\n[TEST 10] CLI gh-tree command")
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = "."

        result = subprocess.run(
            [sys.executable, "-m", "src.cli.cli", "gh-tree", "octocat", "Hello-World"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent,
            env=env
        )

        if result.returncode != 0:
            print(f"  ✗ FAILED: exit code {result.returncode}")
            print(f"    stderr: {result.stderr[:200]}")
            return False

        stdout = result.stdout
        if not stdout:
            print("  ✗ FAILED: empty output")
            return False

        print(f"  ✓ CLI command works")
        lines = stdout.split('\n')[:3]
        for line in lines:
            if line.strip():
                print(f"    {line}")
        return True
    except subprocess.TimeoutExpired:
        print("  ✗ FAILED: timeout")
        return False
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("PHASE 11 — GITHUB INTEGRATION + FILE TREE EXPLORER")
    print("=" * 70)

    tests = [
        test_1_github_client_import,
        test_2_repo_info,
        test_3_file_tree,
        test_4_file_tree_recursive,
        test_5_file_content,
        test_6_pull_requests,
        test_7_api_github_repo,
        test_8_api_github_tree,
        test_9_module_files_exist,
        test_10_cli_gh_tree_command,
    ]

    results = [test() for test in tests]
    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{total} passed")
    print("=" * 70)

    if passed == total:
        print("\n✓ Phase 11 complete. Ready for Phase 12.")
        return 0
    else:
        failed = [i + 1 for i, r in enumerate(results) if not r]
        print(f"\n✗ Failed tests: {', '.join(map(str, failed))}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

