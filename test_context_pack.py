#!/usr/bin/env python
from __future__ import annotations

import json
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parent / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from graph.import_resolver import build_graph
from context.adr_store import load_adrs
from context.context_pack import assemble_context_pack


def main():
    """Test the context pack assembly."""
    
    output = []
    
    # Step 1: Build the dependency graph
    try:
        output.append("Building dependency graph...")
        build_graph("test-codebase")
        output.append("Dependency graph built successfully")
    except Exception as e:
        output.append(f"Error building graph: {e}")
    
    # Step 2: Load ADRs
    try:
        output.append("Loading ADRs...")
        load_adrs("docs/adr")
        output.append("ADRs loaded successfully")
    except Exception as e:
        output.append(f"Error loading ADRs: {e}")
    
    # Step 3: Assemble context pack
    try:
        output.append("Assembling context pack...")
        context_pack = assemble_context_pack(
            task="why is login failing",
            repo_path=".",
        )
        output.append("Context pack assembled successfully")
    except Exception as e:
        output.append(f"Error assembling context pack: {e}")
        import traceback
        output.append(traceback.format_exc())
        context_pack = {}
    
    # Step 4: Pretty-print the context pack
    output.append("\n" + "=" * 80)
    output.append("CONTEXT PACK")
    output.append("=" * 80)
    output.append(json.dumps(context_pack, indent=2, default=str))
    
    # Step 5: Print summary
    output.append("\n" + "=" * 80)
    output.append("SUMMARY")
    output.append("=" * 80)
    chunks = context_pack.get("chunks", [])
    adrs = context_pack.get("adrs", [])
    git_history = context_pack.get("git_history", [])
    dependencies = context_pack.get("background", {}).get("dependencies", [])
    
    output.append(f"Number of chunks found: {len(chunks)}")
    output.append(f"Number of ADRs found: {len(adrs)}")
    output.append(f"Number of git commits found: {len(git_history)}")
    output.append(f"Number of dependencies found: {len(dependencies)}")
    
    # Write to file
    with open("context_pack_test_output.txt", "w") as f:
        f.write("\n".join(output))
    
    # Also try to print
    for line in output:
        print(line)


if __name__ == "__main__":
    main()


