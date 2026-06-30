"""
Side-by-side agent comparison module.
Runs the same task on multiple agents and compares results.
"""

from src.orchestrator.agents import run_agent
from src.context.context_pack import assemble_context_pack


def score_answer(answer: str) -> float:
    """
    Score an answer from 0.0 to 1.0 based on heuristics.

    Scoring breakdown:
    - Length: min(len(answer) / 500, 1.0) * 0.4
    - Code blocks (``` present): +0.2
    - Lists (- or * or numbered): +0.2
    - Specific identifiers (file/function names): +0.1
    - No error: +0.1
    """
    if not answer or len(answer) == 0:
        return round(0.1, 2)

    score = 0.0

    # Length scoring: 0.4
    length_score = min(len(answer) / 500.0, 1.0) * 0.4
    score += length_score

    # Code blocks: +0.2
    if "```" in answer:
        score += 0.2

    # Lists: +0.2
    if ("- " in answer or "* " in answer or
        "\n1. " in answer or "\n2. " in answer):
        score += 0.2

    # Specific identifiers: +0.1
    # Check for patterns like function/file names
    if any(pattern in answer for pattern in [
        ".js", ".ts", ".py", "function", "class ",
        "def ", "const ", "let ", "var "
    ]):
        score += 0.1

    # No error: +0.1
    if "error" not in answer.lower() and "failed" not in answer.lower():
        score += 0.1

    # Cap at 1.0
    return round(min(score, 1.0), 2)


def compare_agents(task: str,
                   agents: list[str],
                   repo_path: str = ".") -> dict:
    """
    Run the same task on multiple agents and compare results.

    Args:
        task: The task to run
        agents: List of agent names to compare
        repo_path: Repository path for context

    Returns:
        {
            "task": task,
            "results": [
                {
                    "agent": "ollama",
                    "answer": "...",
                    "duration_ms": 1200,
                    "tokens_used": 0,
                    "error": None,
                    "score": 0.85
                },
                ...
            ],
            "best_agent": "claude",
            "comparison_summary": "..."
        }
    """
    # Assemble context pack once for all agents
    try:
        context_pack = assemble_context_pack(task, repo_path)
    except Exception as e:
        context_pack = {"task": task, "chunks": [], "error": str(e)}

    # Build a shared prompt with code context for all agents
    chunks_text = ""
    for chunk in context_pack.get("chunks", []):
        chunks_text += f"\n--- {chunk.get('chunk_name')} ({chunk.get('file_path')}) ---\n"
        chunks_text += chunk.get("content", "") + "\n"

    shared_prompt = f"""TASK: {task}

=== RELEVANT CODE FROM CODEBASE ===
{chunks_text}

You are a code analysis expert. Based ONLY on the code above, answer the task. Reference specific function names and code lines. Do not guess."""

    results = []

    # Run each agent
    for agent in agents:
        agent_result = run_agent(agent, shared_prompt, max_tokens=1000)
        # Score the answer
        answer = agent_result.get("answer", "")
        agent_score = score_answer(answer)

        result_entry = {
            "agent": agent,
            "answer": answer,
            "duration_ms": agent_result.get("duration_ms", 0),
            "tokens_used": agent_result.get("tokens_used", 0),
            "error": agent_result.get("error"),
            "score": agent_score
        }
        results.append(result_entry)

    # Find best agent (highest score, then by preference)
    best_agent = None
    best_score = -1
    agent_preference = {"claude": 4, "openai": 3, "codex": 2, "ollama": 1}

    for result in results:
        pref = agent_preference.get(result["agent"], 0)
        if result["score"] > best_score or (
            result["score"] == best_score and pref > agent_preference.get(best_agent, 0)
        ):
            best_score = result["score"]
            best_agent = result["agent"]

    if best_agent is None and results:
        best_agent = results[0]["agent"]

    # Build comparison summary
    if len(results) == 1:
        best_result = results[0]
        comparison_summary = (
            f"{best_result['agent'].capitalize()} answered in "
            f"{best_result['duration_ms']}ms with score {best_result['score']}."
        )
    else:
        sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
        top_agent = sorted_results[0]["agent"]
        top_score = sorted_results[0]["score"]

        if len(sorted_results) > 1:
            second_agent = sorted_results[1]["agent"]
            second_score = sorted_results[1]["score"]
            comparison_summary = (
                f"{top_agent.capitalize()} was best (score {top_score}) vs "
                f"{second_agent.capitalize()} (score {second_score}). "
                f"{top_agent.capitalize()} answered in "
                f"{sorted_results[0]['duration_ms']}ms."
            )
        else:
            comparison_summary = (
                f"{top_agent.capitalize()} scored {top_score} in "
                f"{sorted_results[0]['duration_ms']}ms."
            )

    return {
        "task": task,
        "results": results,
        "best_agent": best_agent,
        "comparison_summary": comparison_summary
    }

