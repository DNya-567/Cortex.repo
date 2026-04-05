from __future__ import annotations

import json
from pathlib import Path

from src.context.context_pack import assemble_context_pack
from src.context.adr_store import load_adrs
from src.graph.import_resolver import build_graph


def main():
    """Test the context pack assembly."""

    project_root = Path(__file__).resolve().parents[2]

    # Step 1: Build the dependency graph
    print("Building dependency graph...")
    build_graph(str(project_root / "test-codebase"))

    # Step 2: Load ADRs
    print("Loading ADRs...")
    load_adrs(str(project_root / "docs" / "adr"))

    # Step 3: Assemble context pack
    print("Assembling context pack...")
    context_pack = assemble_context_pack(
        task="why is login failing",
        repo_path=str(project_root),
    )

    # Step 4: Pretty-print the context pack
    print("\n" + "=" * 80)
    print("CONTEXT PACK")
    print("=" * 80)
    print(json.dumps(context_pack, indent=2, default=str))

    # Step 5: Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    chunks = context_pack.get("chunks", [])
    adrs = context_pack.get("adrs", [])
    git_history = context_pack.get("git_history", [])
    dependencies = context_pack.get("background", {}).get("dependencies", [])

    print(f"Number of chunks found: {len(chunks)}")
    print(f"Number of ADRs found: {len(adrs)}")
    print(f"Number of git commits found: {len(git_history)}")
    print(f"Number of dependencies found: {len(dependencies)}")


if __name__ == "__main__":
    main()



