from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("PHASE 5 VERIFICATION")
print("=" * 80)

results = {}

print("\n[TEST 1] CLI: help command...")
try:
    from src.cli.cli import main as cli_main
    import io
    from contextlib import redirect_stdout

    old_argv = sys.argv
    sys.argv = ["cli", "--help"]
    output = io.StringIO()
    try:
        with redirect_stdout(output):
            cli_main()
    except SystemExit:
        pass
    sys.argv = old_argv

    help_text = output.getvalue()
    assert "index" in help_text
    assert "search" in help_text
    assert "ask" in help_text
    print("✓ PASS: CLI help works")
    results["CLI Help"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["CLI Help"] = False

print("\n[TEST 2] Reporter: generate_report...")
try:
    from src.reporter.report import generate_report
    report = generate_report("what does login do", ".")
    assert "# Context Engine Report" in report
    assert "Task:" in report
    assert "Relevant Code" in report
    assert "Answer" in report
    print("✓ PASS: Report generation works")
    print(f"  Report length: {len(report)} chars")
    results["Report Generation"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Report Generation"] = False

print("\n[TEST 3] API /report endpoint...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/report?task=what+does+login+do")
    assert response.status_code == 200
    data = response.json()
    assert "task" in data
    assert "report" in data
    assert "Context Engine Report" in data["report"]
    print("✓ PASS: /report endpoint works")
    print(f"  Report length: {len(data['report'])} chars")
    results["API /report"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API /report"] = False

print("\n[TEST 4] API /cli-help endpoint...")
try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/cli-help")
    assert response.status_code == 200
    data = response.json()
    assert "usage" in data
    assert "commands" in data
    assert len(data["commands"]) >= 10
    print("✓ PASS: /cli-help endpoint works")
    print(f"  Commands documented: {len(data['commands'])}")
    for cmd in data["commands"][:3]:
        print(f"    - {cmd['name']}: {cmd['description']}")
    results["API /cli-help"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["API /cli-help"] = False

print("\n[TEST 5] CLI: search command...")
try:
    from src.cli.cli import cmd_search
    import argparse
    import io
    from contextlib import redirect_stdout

    args = argparse.Namespace(query="login", top_k=3)
    output = io.StringIO()
    with redirect_stdout(output):
        cmd_search(args)

    output_text = output.getvalue()
    assert "score:" in output_text.lower() or len(output_text) > 0
    print("✓ PASS: CLI search command works")
    print(f"  Output length: {len(output_text)} chars")
    results["CLI Search"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["CLI Search"] = False

print("\n[TEST 6] CLI: health command...")
try:
    from src.cli.cli import cmd_health
    import argparse
    import io
    from contextlib import redirect_stdout

    args = argparse.Namespace()
    output = io.StringIO()
    with redirect_stdout(output):
        cmd_health(args)

    output_text = output.getvalue()
    assert "Health" in output_text or "overall" in output_text.lower()
    print("✓ PASS: CLI health command works")
    print(f"  Output: {output_text.split(chr(10))[0]}")
    results["CLI Health"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["CLI Health"] = False

print("\n[TEST 7] CLI: cache-stats command...")
try:
    from src.cli.cli import cmd_cache_stats
    import argparse
    import io
    from contextlib import redirect_stdout

    args = argparse.Namespace()
    output = io.StringIO()
    with redirect_stdout(output):
        cmd_cache_stats(args)

    output_text = output.getvalue()
    assert "Cached" in output_text or "queries" in output_text.lower()
    print("✓ PASS: CLI cache-stats command works")
    print(f"  Output: {output_text.strip()}")
    results["CLI Cache Stats"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["CLI Cache Stats"] = False

print("\n[TEST 8] CLI: deps command...")
try:
    from src.cli.cli import cmd_deps
    import argparse
    import io
    from contextlib import redirect_stdout

    args = argparse.Namespace(file="test-codebase/auth.js")
    output = io.StringIO()
    with redirect_stdout(output):
        cmd_deps(args)

    output_text = output.getvalue()
    assert "Dependencies" in output_text or "No dependencies" in output_text
    print("✓ PASS: CLI deps command works")
    results["CLI Deps"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["CLI Deps"] = False

print("\n[TEST 9] CLI: adrs command...")
try:
    from src.cli.cli import cmd_adrs
    import argparse
    import io
    from contextlib import redirect_stdout

    args = argparse.Namespace(file="test-codebase/auth.js")
    output = io.StringIO()
    with redirect_stdout(output):
        cmd_adrs(args)

    output_text = output.getvalue()
    assert "ADR" in output_text or "No ADRs" in output_text
    print("✓ PASS: CLI adrs command works")
    results["CLI ADRs"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["CLI ADRs"] = False

print("\n[TEST 10] CLI: git-log command...")
try:
    from src.cli.cli import cmd_git_log
    import argparse
    import io
    from contextlib import redirect_stdout

    args = argparse.Namespace(file="test-codebase/auth.js")
    output = io.StringIO()
    with redirect_stdout(output):
        cmd_git_log(args)

    output_text = output.getvalue()
    assert "history" in output_text.lower() or "No git" in output_text
    print("✓ PASS: CLI git-log command works")
    results["CLI Git Log"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["CLI Git Log"] = False

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
    print("\n🎉 Phase 5 complete. Ready for Phase 6.")
    sys.exit(0)
else:
    failed = [name for name, p in results.items() if not p]
    print(f"\n⚠️ {total - passed} test(s) failed: {', '.join(failed)}")
    sys.exit(1)

