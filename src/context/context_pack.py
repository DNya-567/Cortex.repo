from __future__ import annotations

from src.search.searcher import search
from src.graph.import_resolver import get_dependencies
from src.context.adr_store import get_adrs_for_file
from src.context.git_log import get_file_history


def assemble_context_pack(task: str, repo_path: str) -> dict:
    """
    Assemble a comprehensive context pack for a given task.

    The context pack includes:
    1. Task description
    2. Background: upstream dependencies
    3. ADRs: architectural decisions
    4. Git history: recent commits
    5. Code chunks: semantically relevant code
    6. Instruction: formatted task prompt

    Returns a dict with all context organized from least to most critical.
    """

    # Step 1: Search for relevant chunks
    chunks = search(query=task, top_k=5)

    # Step 2: Collect dependencies, ADRs, and git history for each chunk's file
    all_dependencies = []
    all_adrs = []
    all_git_history = []

    seen_files = set()

    for chunk in chunks:
        file_path = chunk.get("file_path", "")
        if file_path in seen_files:
            continue
        seen_files.add(file_path)

        # Get upstream dependencies
        deps = get_dependencies(file_path)
        for dep in deps:
            if dep not in all_dependencies:
                all_dependencies.append(dep)

        # Get relevant ADRs
        adrs = get_adrs_for_file(file_path)
        for adr in adrs:
            # Check if already in list (by adr_id)
            if not any(a.get("adr_id") == adr.get("adr_id") for a in all_adrs):
                all_adrs.append(adr)

        # Get git history
        git_commits = get_file_history(repo_path, file_path, limit=3)
        for commit in git_commits:
            # Check if already in list (by commit_hash)
            if not any(c.get("commit_hash") == commit.get("commit_hash") for c in all_git_history):
                all_git_history.append(commit)

    # Step 3: Assemble context pack in order (least critical first)
    context_pack = {
        "task": task,
        "background": {
            "dependencies": all_dependencies,
        },
        "adrs": all_adrs,
        "git_history": all_git_history,
        "chunks": chunks,
        "instruction": f"Based on the above context, {task}",
    }

    return context_pack

