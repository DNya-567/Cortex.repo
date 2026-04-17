#!/usr/bin/env python3
"""
Context Engine — Master Test Runner
Runs all verification tests in sequence and gives final report.

Usage:
    $env:PYTHONPATH="."; venv\Scripts\python.exe run_all_tests.py
"""

import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime

def run_test(phase_num, script_name):
    """Run a single test script and return pass/fail."""
    print(f"\n{'='*80}")
    print(f"RUNNING: Phase {phase_num} ({script_name})")
    print('='*80)

    env = os.environ.copy()
    env["PYTHONPATH"] = "."

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=str(Path(__file__).parent),
            env=env,
            timeout=120,  # 2 minute timeout per test
            capture_output=False
        )

        passed = result.returncode == 0
        return passed, None
    except subprocess.TimeoutExpired:
        return False, "Test timeout (>2 min)"
    except Exception as e:
        return False, str(e)

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   CONTEXT ENGINE — MASTER TEST SUITE                       ║
║                                                                            ║
║  Prerequisites: Ollama & Qdrant running                                   ║
║  $env:PYTHONPATH="."  set in PowerShell                                    ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    start_time = datetime.now()

    tests = [
        (1, "verify_phase2.py", "Core Chunking & Indexing"),
        (2, "verify_phase3.py", "Dependency Graph & Context"),
        (3, "verify_phase4.py", "API Endpoints & Cache"),
        (4, "verify_phase5.py", "CLI Commands"),
        (5, "verify_phase6.py", "VS Code Extension"),
        (6, "verify_phase7.py", "Multi-Language Chunking"),
        (7, "verify_phase8.py", "Streaming (SSE)"),
        (8, "verify_phase9.py", "Authentication & Rate Limiting"),
        (9, "verify_phase10.py", "Production Files"),
        (10, "verify_phase11.py", "GitHub Integration"),
    ]

    results = {}
    failed_tests = []

    for phase_num, script, description in tests:
        passed, error = run_test(phase_num, script)
        results[f"Phase {phase_num}: {description}"] = (passed, error)

        if not passed:
            failed_tests.append((phase_num, description, error))

    elapsed = (datetime.now() - start_time).total_seconds()

    # Print summary
    print(f"\n\n{'='*80}")
    print("FINAL RESULTS")
    print('='*80)

    passed_count = sum(1 for p, _ in results.values() if p)
    total_count = len(results)

    for test_name, (passed, error) in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if error:
            print(f"         Error: {error}")

    print(f"\n{'─'*80}")
    print(f"Total: {passed_count}/{total_count} tests passed")
    print(f"Time: {elapsed:.1f} seconds")
    print('='*80)

    if passed_count == total_count:
        print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                          🎉 ALL TESTS PASSED! 🎉                          ║
║                                                                            ║
║  Your Context Engine is working correctly!                                ║
║                                                                            ║
║  Next steps:                                                              ║
║  1. Start API: uvicorn src.api.main:app --port 8000                       ║
║  2. Open: http://localhost:8000/dashboard.html                            ║
║  3. Try: python -m src.cli.cli ask "your question here"                   ║
║                                                                            ║
║  For VS Code extension:                                                   ║
║  - Open vscode-extension/ folder in VS Code                               ║
║  - Press F5 to start debugging                                            ║
║  - Ctrl+Shift+P → "Context Engine: Open Panel"                            ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
        """)
        return 0
    else:
        print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    ⚠️  {total_count - passed_count} TEST(S) FAILED  ⚠️                    ║
║                                                                            ║
║  Failed tests:                                                            ║""")
        for phase_num, description, error in failed_tests:
            print(f"║  - Phase {phase_num}: {description}")
            if error:
                print(f"║    {error[:70]}")
        print("""║                                                                            ║
║  Troubleshooting:                                                         ║
║  1. Check Ollama is running: ollama serve                                 ║
║  2. Check Qdrant is running: docker run -p 6333:6333 qdrant/qdrant       ║
║  3. Check PYTHONPATH: $env:PYTHONPATH="."                                 ║
║  4. Review TESTING_GUIDE.md for detailed help                             ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
        """)
        return 1

if __name__ == "__main__":
    sys.exit(main())

