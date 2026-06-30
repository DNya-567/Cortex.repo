#!/usr/bin/env python3
"""
Quick test to verify health check logic is fixed.
Run: $env:PYTHONPATH="."; venv\Scripts\python.exe tests\verification\test_health_fix.py
"""

import sys
sys.path.insert(0, '.')

from src.health.checker import check_health

def test_health_check():
    """Test that health check returns correct overall status."""
    result = check_health()

    print("=" * 60)
    print("HEALTH CHECK TEST")
    print("=" * 60)

    # Print individual service status
    print("\nService Status:")
    print(f"  Ollama:            {result['ollama']['status']:10} - {result['ollama']['message']}")
    print(f"  Qdrant:            {result['qdrant']['status']:10} - {result['qdrant']['message']}")
    print(f"  Qdrant Collection: {result['qdrant_collection']['status']:10} - {result['qdrant_collection']['message']}")
    print(f"  SQLite:            {result['sqlite']['status']:10} - {result['sqlite']['message']}")

    # Print overall status
    print(f"\nOverall Status: {result['overall'].upper()}")

    # Verify logic
    statuses = [
        result['ollama']['status'],
        result['qdrant']['status'],
        result['qdrant_collection']['status'],
        result['sqlite']['status'],
    ]
    ok_count = sum(1 for s in statuses if s == 'ok')
    total = len(statuses)

    print(f"\nLogic Verification:")
    print(f"  Services OK: {ok_count}/{total}")

    # Check the logic
    if ok_count == total:
        expected = "ok"
        print(f"  Expected: ok (all services healthy)")
    elif ok_count > 0:
        expected = "degraded"
        print(f"  Expected: degraded ({ok_count} services up, {total - ok_count} down)")
    else:
        expected = "error"
        print(f"  Expected: error (all services down)")

    # Verify
    if result['overall'] == expected:
        print(f"\n✓ PASS: Overall status is correct ({result['overall']})")
        return True
    else:
        print(f"\n✗ FAIL: Expected '{expected}' but got '{result['overall']}'")
        return False

if __name__ == '__main__':
    success = test_health_check()
    print("=" * 60)
    sys.exit(0 if success else 1)

