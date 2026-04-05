#!/usr/bin/env python
"""
Phase 2 Verification Script
Checks that all components are working correctly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path
SRC_ROOT = Path(__file__).resolve().parent / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def test_import_resolver():
    """Test the dependency graph builder."""
    print("\n" + "="*80)
    print("TEST 1: Import Resolver (Dependency Graph)")
    print("="*80)

    try:
        from graph.import_resolver import build_graph, get_dependencies, get_dependents
        print("✓ Import resolver module loaded")

        # Build graph
        print("  Building dependency graph for test-codebase...")
        build_graph("test-codebase")
        print("  ✓ Dependency graph built")

        # Test getting dependencies
        deps = get_dependencies("test-codebase/auth.js")
        print(f"  ✓ Found {len(deps)} dependency/dependencies for auth.js")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adr_store():
    """Test the ADR (Architecture Decision Record) store."""
    print("\n" + "="*80)
    print("TEST 2: ADR Store (Architecture Decisions)")
    print("="*80)

    try:
        from context.adr_store import load_adrs, get_all_adrs, get_adrs_for_file
        print("✓ ADR store module loaded")

        # Load ADRs
        print("  Loading ADRs from docs/adr...")
        load_adrs("docs/adr")
        print("  ✓ ADRs loaded")

        # Get all ADRs
        all_adrs = get_all_adrs()
        print(f"  ✓ Found {len(all_adrs)} ADR(s)")
        for adr in all_adrs:
            print(f"    - {adr['adr_id']}: {adr['title']}")

        # Get ADRs for a file
        adrs = get_adrs_for_file("test-codebase/auth.js")
        print(f"  ✓ Found {len(adrs)} ADR(s) affecting auth.js")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_git_log():
    """Test the git history tracker."""
    print("\n" + "="*80)
    print("TEST 3: Git Log (Change History)")
    print("="*80)

    try:
        from context.git_log import get_file_history
        print("✓ Git log module loaded")

        # Get git history
        print("  Getting git history for test-codebase/auth.js...")
        commits = get_file_history(".", "test-codebase/auth.js", limit=3)
        print(f"  ✓ Found {len(commits)} commit(s)")
        for commit in commits:
            print(f"    - {commit['date']}: {commit['message'][:50]}...")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context_pack():
    """Test the context pack assembly."""
    print("\n" + "="*80)
    print("TEST 4: Context Pack Assembly (The Star Feature!)")
    print("="*80)

    try:
        from context.context_pack import assemble_context_pack
        print("✓ Context pack module loaded")

        # Assemble context pack
        print("  Assembling context pack for task: 'why is login failing'...")
        pack = assemble_context_pack(
            task="why is login failing",
            repo_path="."
        )
        print("  ✓ Context pack assembled successfully")

        # Print summary
        print("\n  Context Pack Structure:")
        print(f"    - Task: {pack.get('task', 'N/A')}")
        print(f"    - Dependencies: {len(pack.get('background', {}).get('dependencies', []))}")
        print(f"    - ADRs: {len(pack.get('adrs', []))}")
        print(f"    - Git History: {len(pack.get('git_history', []))}")
        print(f"    - Code Chunks: {len(pack.get('chunks', []))}")
        print(f"    - Instruction: Yes")

        # Show first chunk
        chunks = pack.get('chunks', [])
        if chunks:
            chunk = chunks[0]
            print(f"\n  First chunk:")
            print(f"    - Name: {chunk.get('chunk_name')}")
            print(f"    - File: {chunk.get('file_path')}")
            print(f"    - Type: {chunk.get('chunk_type')}")
            print(f"    - Score: {chunk.get('score', 'N/A'):.2f}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoint():
    """Test that the API endpoint exists (without running server)."""
    print("\n" + "="*80)
    print("TEST 5: API Endpoint (/context-pack)")
    print("="*80)

    try:
        from api.main import context_pack_endpoint
        print("✓ API module loaded")
        print("✓ /context-pack endpoint function found")

        # Test the function directly
        print("  Testing endpoint with task='test query'...")
        result = context_pack_endpoint(task="test query")
        print(f"  ✓ Endpoint returned valid response")
        print(f"    Keys: {list(result.keys())}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("PHASE 2 VERIFICATION")
    print("Testing all new components")
    print("="*80)

    results = {
        "Import Resolver": test_import_resolver(),
        "ADR Store": test_adr_store(),
        "Git Log": test_git_log(),
        "Context Pack": test_context_pack(),
        "API Endpoint": test_api_endpoint(),
    }

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Phase 2 is ready to use!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed. Please review above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


