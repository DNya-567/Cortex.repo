import sqlite3
import os

print("\n=== DATABASE TABLES ===")
try:
    conn = sqlite3.connect("graph.db")
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    if tables:
        for t in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
            print(f"  {t[0]}: {count} rows")
    else:
        print("  No tables found")
    conn.close()
except Exception as e:
    print(f"  Error: {e}")

print("\n=== ORCHESTRATOR FILES ===")
orch_dir = "src/orchestrator"
if os.path.exists(orch_dir):
    for f in os.listdir(orch_dir):
        full = os.path.join(orch_dir, f)
        size = os.path.getsize(full)
        print(f"  {f}: {size} bytes")
else:
    print("  Directory not found")

print("\n=== ALL SRC FILES ===")
for root, dirs, files in os.walk("src"):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for f in files:
        if f.endswith(".py"):
            full = os.path.join(root, f)
            size = os.path.getsize(full)
            print(f"  {full}: {size} bytes")

print("\n=== VERIFY FILES ===")
for f in os.listdir("."):
    if f.startswith("verify"):
        size = os.path.getsize(f)
        print(f"  {f}: {size} bytes")

print("\nDone.")
