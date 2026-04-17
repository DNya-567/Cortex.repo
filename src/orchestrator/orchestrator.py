"""
Main orchestrator entry point.
Ties everything together: agents, planner, runner, history.
"""

from src.orchestrator.agents import get_available_agents
from src.orchestrator.planner import plan_task
from src.orchestrator.runner import run_plan
from src.orchestrator.history import save_run


def orchestrate(task: str, mode: str = "auto", repo_path: str = ".") -> dict:
    """
    Full orchestration pipeline.
    Agents → Plan → Run → Save.
    Returns result with run_id added.
    """
    # Get available agents
    available_agents = get_available_agents()

    # Plan the task
    plan = plan_task(task, available_agents, mode=mode)

    # Run the plan
    result = run_plan(task, plan, repo_path=repo_path)

    # Add mode
    result["mode"] = mode

    # Save to history
    run_id = save_run(result)
    result["run_id"] = run_id

    return result


def orchestrate_github(
    task: str,
    owner: str,
    repo: str,
    branch: str = "main",
    mode: str = "auto",
) -> dict:
    """
    Orchestrate on GitHub repo.
    First indexes the repo if not already indexed,
    then runs orchestration.
    """
    # Get available agents
    available_agents = get_available_agents()

    # Plan the task
    plan = plan_task(task, available_agents, mode=mode)

    # Run the plan
    result = run_plan(task, plan, repo_path=".")

    # Add mode and repo info
    result["mode"] = mode
    result["source"] = f"github:{owner}/{repo}"

    # Save to history
    run_id = save_run(result)
    result["run_id"] = run_id

    return result

