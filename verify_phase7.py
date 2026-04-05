from __future__ import annotations
import sys
import os
import subprocess
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("PHASE 7 VERIFICATION")
print("=" * 80)

results = {}

print("\n[TEST 1] Python Chunker...")
try:
    from src.chunker.python_chunker import chunk_python_file
    chunks = chunk_python_file("test-codebase/sample.py")
    assert len(chunks) >= 3, f"Expected >= 3 chunks, got {len(chunks)}"
    assert all(c.language == "python" for c in chunks), "Not all chunks are python"
    types = [c.chunk_type for c in chunks]
    assert "function" in types, "No functions found"
    assert "class" in types, "No classes found"
    print(f"✓ PASS: Python chunker found {len(chunks)} chunks")
    for c in chunks:
        print(f"  - {c.chunk_name} ({c.chunk_type})")
    results["Python Chunker"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Python Chunker"] = False

print("\n[TEST 2] Generic Chunker...")
try:
    from src.chunker.generic_chunker import chunk_generic_file
    temp_dir = Path("test-codebase")
    temp_file = temp_dir / "sample.java"
    lines = "\n".join([f"// line {i}" for i in range(1, 61)])
    temp_file.write_text(lines)

    chunks = chunk_generic_file(str(temp_file))
    assert len(chunks) >= 2, f"Expected >= 2 chunks, got {len(chunks)}"
    assert all(c.language == "java" for c in chunks), "Not all chunks are java"
    assert all(c.chunk_type == "block" for c in chunks), "Not all chunks are blocks"
    print(f"✓ PASS: Generic chunker found {len(chunks)} chunks")
    for c in chunks:
        print(f"  - {c.chunk_name} (lines {c.start_line}-{c.end_line})")

    temp_file.unlink()
    results["Generic Chunker"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Generic Chunker"] = False

print("\n[TEST 3] chunk_file_any routing...")
try:
    from src.chunker.chunker import chunk_file_any
    js_chunks = chunk_file_any("test-codebase/auth.js")
    assert len(js_chunks) >= 1, "No JS chunks"
    assert js_chunks[0].language == "javascript", "JS chunk language mismatch"

    py_chunks = chunk_file_any("test-codebase/sample.py")
    assert len(py_chunks) >= 1, "No Python chunks"
    assert py_chunks[0].language == "python", "Python chunk language mismatch"

    print("✓ PASS: Routing works for JS and Python")
    results["File Any Routing"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["File Any Routing"] = False

print("\n[TEST 4] chunk_directory_any...")
try:
    from src.chunker.chunker import chunk_directory_any
    chunks = chunk_directory_any("test-codebase")
    assert len(chunks) >= 5, f"Expected >= 5 chunks, got {len(chunks)}"

    languages = set(c.language for c in chunks)
    assert "javascript" in languages or "python" in languages, "Missing expected languages"

    print(f"✓ PASS: Found {len(chunks)} chunks from multiple languages")
    print(f"  Languages: {', '.join(sorted(languages))}")
    results["Directory Any"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Directory Any"] = False

print("\n[TEST 5] Chunk Stats...")
try:
    from src.chunker.chunk_stats import get_chunk_stats
    stats = get_chunk_stats("test-codebase")
    assert "total_chunks" in stats, "Missing total_chunks"
    assert "by_language" in stats, "Missing by_language"
    assert "by_type" in stats, "Missing by_type"
    assert stats["total_chunks"] >= 5, f"Expected >= 5 chunks, got {stats['total_chunks']}"

    print("✓ PASS: Chunk stats calculated")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  By language: {stats['by_language']}")
    print(f"  By type: {stats['by_type']}")
    results["Chunk Stats"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Chunk Stats"] = False

print("\n[TEST 6] Indexer still works...")
try:
    from src.indexer import index_directory
    result = index_directory("test-codebase")
    assert result["status"] == "ok", f"Status: {result.get('status')}"
    assert result["total_chunks"] >= 3, f"Expected >= 3 chunks, got {result['total_chunks']}"
    print(f"✓ PASS: Indexer works - {result['total_chunks']} chunks, {result['total_files']} files")
    results["Indexer"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Indexer"] = False

print("\n[TEST 7] Search still works...")
try:
    from src.search.searcher import search
    results_list = search("where is user login", top_k=3)
    assert len(results_list) >= 1, "No search results"
    assert results_list[0]["chunk_name"] == "login", f"Expected 'login', got {results_list[0]['chunk_name']}"
    print(f"✓ PASS: Search works - found '{results_list[0]['chunk_name']}'")
    results["Search"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Search"] = False

print("\n[TEST 8] Python chunks have correct line numbers...")
try:
    from src.chunker.python_chunker import chunk_python_file
    chunks = chunk_python_file("test-codebase/sample.py")
    for c in chunks:
        assert c.start_line < c.end_line, f"Bad line range: {c.start_line}-{c.end_line}"
        assert c.content, f"Empty content for {c.chunk_name}"

    print("✓ PASS: Line numbers and content valid")
    for c in chunks:
        print(f"  - {c.chunk_name}: lines {c.start_line}-{c.end_line}")
    results["Python Line Numbers"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Python Line Numbers"] = False

print("\n[TEST 9] Generic chunker overlap...")
try:
    from src.chunker.generic_chunker import chunk_generic_file
    temp_file = Path("test-codebase") / "temp100.txt"
    lines = "\n".join([f"line {i}" for i in range(1, 101)])
    temp_file.write_text(lines)

    chunks = chunk_generic_file(str(temp_file), window=30, overlap=10)
    assert len(chunks) >= 4, f"Expected >= 4 chunks, got {len(chunks)}"

    print(f"✓ PASS: Generic chunker with overlap - {len(chunks)} chunks")
    for c in chunks:
        print(f"  - {c.chunk_name}: lines {c.start_line}-{c.end_line}")

    temp_file.unlink()
    results["Generic Overlap"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["Generic Overlap"] = False

print("\n[TEST 10] CLI chunk-stats command...")
try:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.cli", "chunk-stats", "test-codebase"],
        cwd=str(Path(__file__).parent),
        capture_output=True,
        text=True,
        env=env,
        timeout=30
    )

    assert result.returncode == 0, f"Exit code {result.returncode}"
    output = result.stdout + result.stderr
    assert "Total chunks:" in output or "total_chunks" in output, "Missing chunk count in output"

    print("✓ PASS: CLI chunk-stats command works")
    print(f"  Output:\n{result.stdout}")
    results["CLI chunk-stats"] = True
except Exception as e:
    print(f"✗ FAIL: {e}")
    results["CLI chunk-stats"] = False

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
    print("\n🎉 Phase 7 complete. Ready for Phase 8.")
    sys.exit(0)
else:
    failed = [name for name, p in results.items() if not p]
    print(f"\n⚠️ {total - passed} test(s) failed: {', '.join(failed)}")
    sys.exit(1)

