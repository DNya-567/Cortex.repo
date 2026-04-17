"""
Execute an orchestration plan.
Runs each subtask, collects results, merges into final answer.
"""

import time
from src.orchestrator.agents import run_agent
from src.context.context_pack import assemble_context_pack


def run_plan(task: str, plan: list[dict], repo_path: str = ".") -> dict:
    """
    Execute the plan — run each subtask and collect results.
    Returns dict with: task, mode, subtasks, final_answer,
    total_duration_ms, agents_used, context_used
    """
    start_time = time.time()

    # Assemble context once
    try:
        context_pack = assemble_context_pack(task, repo_path)
    except Exception as e:
        context_pack = {
            "task": task,
            "chunks": [],
            "adrs": [],
            "background": {"dependencies": []},
            "git_history": [],
            "instruction": task,
        }

    context_used = {
        "chunks": len(context_pack.get("chunks", [])),
        "adrs": len(context_pack.get("adrs", [])),
        "dependencies": len(context_pack.get("background", {}).get("dependencies", [])),
        "git_commits": len(context_pack.get("git_history", [])),
    }

    # Truncate context to 2000 chars to avoid overwhelming models
    context_str = _truncate_context(context_pack, 2000)

    # Run each subtask
    subtasks_results = []
    agents_used = set()
    previous_answers = []

    for subtask in plan:
        agent = subtask["agent"]
        agents_used.add(agent)

        # Build prompt based on subtask type
        prompt = _build_prompt(
            subtask, task, context_str, previous_answers
        )

        # Run agent
        result = run_agent(agent, prompt, max_tokens=1000)

        # Store result
        subtask_result = {
            "subtask_id": subtask["subtask_id"],
            "description": subtask["description"],
            "agent": agent,
            "answer": result["answer"],
            "duration_ms": result["duration_ms"],
            "error": result["error"],
        }
        subtasks_results.append(subtask_result)
        previous_answers.append(result["answer"])

    # Merge final answer
    final_answer = _merge_answers(subtasks_results)

    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "task": task,
        "mode": "orchestrated",
        "subtasks": subtasks_results,
        "final_answer": final_answer,
        "total_duration_ms": elapsed_ms,
        "agents_used": list(agents_used),
        "context_used": context_used,
    }


def _truncate_context(context_pack: dict, max_chars: int) -> str:
    """Convert context pack to string and truncate."""
    parts = []

    if context_pack.get("chunks"):
        parts.append("CODE CHUNKS:")
        for chunk in context_pack["chunks"][:3]:  # First 3 chunks
            parts.append(f"  - {chunk.get('chunk_name')}: {chunk.get('content', '')[:200]}")

    if context_pack.get("adrs"):
        parts.append("ARCHITECTURE DECISIONS:")
        for adr in context_pack["adrs"][:2]:
            parts.append(f"  - {adr.get('title')}: {adr.get('decision', '')[:150]}")

    result = "\n".join(parts)
    return result[:max_chars]


def _build_prompt(
    subtask: dict, task: str, context_str: str, previous_answers: list
) -> str:
    """Build prompt based on subtask type."""
    prompt_type = subtask["prompt_type"]

    if prompt_type == "search":
        return f"""Find and list relevant code for this task:
{task}

Context available:
{context_str}

List the relevant code sections or files."""

    elif prompt_type == "explain":
        prev = "\n".join(previous_answers) if previous_answers else "No previous findings"
        return f"""Explain this code and task clearly:
Task: {task}

Previous findings:
{prev}

Context:
{context_str}

Provide a clear explanation."""

    elif prompt_type == "improve":
        prev = "\n".join(previous_answers) if previous_answers else "No issues identified"
        return f"""Suggest specific improvements for this task:
Task: {task}

Issues found:
{prev}

Code context:
{context_str}

Provide concrete, actionable suggestions."""

    elif prompt_type == "review":
        return f"""Review this code for issues:
Task: {task}

Code context:
{context_str}

Identify potential bugs, performance issues, and best practice violations."""

    elif prompt_type == "summarize":
        all_findings = "\n".join(previous_answers) if previous_answers else "No findings"
        return f"""Summarize the findings for this task:
Task: {task}

All findings:
{all_findings}

Provide a concise, actionable summary."""

    else:
        return f"""{task}

Context:
{context_str}"""


def _merge_answers(subtasks_results: list) -> str:
    """Merge subtask answers into final answer."""
    if not subtasks_results:
        return "No results"

    if len(subtasks_results) == 1:
        return subtasks_results[0]["answer"]

    # Multiple subtasks: concatenate with headers
    parts = []
    headers = ["Finding", "Analysis", "Improvements", "Review", "Summary"]

    for i, result in enumerate(subtasks_results):
        header = headers[i] if i < len(headers) else f"Result {i + 1}"
        if result["error"]:
            parts.append(f"## {header}\n[ERROR: {result['error']}]")
        else:
            parts.append(f"## {header}\n{result['answer']}")

    return "\n\n".join(parts)

