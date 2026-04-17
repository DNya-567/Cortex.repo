"""Task decomposition planner - breaks tasks into subtasks and assigns agents."""


def plan_task(
    task: str, available_agents: list[str], mode: str = "auto"
) -> list[dict]:
    """
    Decompose a task into subtasks and assign agents.

    Returns list of subtasks with: subtask_id, description, agent,
    prompt_type, priority
    """
    task_lower = task.lower()

    # Determine subtasks based on task type
    if any(k in task_lower for k in ["explain", "how", "why", "describe"]):
        subtasks = [
            {"subtask_id": 1, "description": f"Find relevant code: {task}",
             "agent": None, "prompt_type": "search", "priority": 1},
            {"subtask_id": 2, "description": f"Explain findings: {task}",
             "agent": None, "prompt_type": "explain", "priority": 2},
        ]
    elif any(k in task_lower for k in ["fix", "refactor", "improve", "optimize"]):
        subtasks = [
            {"subtask_id": 1, "description": f"Find relevant code: {task}",
             "agent": None, "prompt_type": "search", "priority": 1},
            {"subtask_id": 2, "description": f"Review code: {task}",
             "agent": None, "prompt_type": "review", "priority": 2},
            {"subtask_id": 3, "description": f"Suggest improvements: {task}",
             "agent": None, "prompt_type": "improve", "priority": 3},
        ]
    elif any(k in task_lower for k in ["list", "what", "show", "find"]):
        subtasks = [
            {"subtask_id": 1, "description": f"Find and list: {task}",
             "agent": None, "prompt_type": "search", "priority": 1},
        ]
    else:
        subtasks = [
            {"subtask_id": 1, "description": f"Find relevant code: {task}",
             "agent": None, "prompt_type": "search", "priority": 1},
            {"subtask_id": 2, "description": f"Analyze and explain: {task}",
             "agent": None, "prompt_type": "explain", "priority": 2},
        ]

    # Assign agents based on mode
    if mode == "collaborative":
        for i, subtask in enumerate(subtasks):
            if available_agents:
                subtask["agent"] = available_agents[i % len(available_agents)]
    elif mode in ["ollama", "claude", "openai", "codex"]:
        forced_agent = mode if mode in available_agents else (available_agents[0] if available_agents else "ollama")
        for subtask in subtasks:
            subtask["agent"] = forced_agent
    else:
        # Auto-routing based on task type
        for subtask in subtasks:
            ptype = subtask["prompt_type"]
            default_agent = available_agents[0] if available_agents else "ollama"

            if ptype == "search":
                subtask["agent"] = "ollama" if "ollama" in available_agents else default_agent
            elif ptype == "explain":
                subtask["agent"] = "claude" if "claude" in available_agents else (
                    "ollama" if "ollama" in available_agents else default_agent
                )
            elif ptype == "improve":
                if "codex" in available_agents:
                    subtask["agent"] = "codex"
                elif "openai" in available_agents:
                    subtask["agent"] = "openai"
                else:
                    subtask["agent"] = "ollama" if "ollama" in available_agents else default_agent
            elif ptype == "review":
                if "claude" in available_agents:
                    subtask["agent"] = "claude"
                elif "openai" in available_agents:
                    subtask["agent"] = "openai"
                else:
                    subtask["agent"] = "ollama" if "ollama" in available_agents else default_agent
            else:
                subtask["agent"] = default_agent

    return subtasks

