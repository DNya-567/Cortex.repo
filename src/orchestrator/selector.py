"""
Agent recommendation and selection module.
Recommends the best agent for a given task type.
"""

import re


def _detect_task_type(task: str) -> str:
    """
    Detect task type from task string using keyword matching.

    Returns one of: search, explain, improve, review, generate, compare, general
    """
    task_lower = task.lower()

    # Search/find/locate tasks
    if re.search(r'\b(search|find|where|list|show|locate|get|retrieve)\b', task_lower):
        return "search"

    # Explain/understand tasks
    if re.search(r'\b(explain|how|why|what does|understand|describe|tell me)\b', task_lower):
        return "explain"

    # Fix/improve tasks
    if re.search(r'\b(fix|refactor|improve|optimize|enhance|better|rewrite)\b', task_lower):
        return "improve"

    # Review/audit tasks
    if re.search(r'\b(review|check|audit|test|validate|verify|inspect)\b', task_lower):
        return "review"

    # Generate/create tasks
    if re.search(r'\b(generate|write|create|build|make|implement|code)\b', task_lower):
        return "generate"

    # Compare tasks
    if re.search(r'\b(compare|difference|vs|versus|contrast|similar)\b', task_lower):
        return "compare"

    return "general"


def recommend_agent(task: str,
                    available: list[str]) -> dict:
    """
    Recommend the best agent for a task based on task type and availability.

    Args:
        task: The task description
        available: List of available agent names

    Returns:
        {
            "recommended": "ollama",
            "reason": "Task is a simple code search query...",
            "alternatives": ["claude"],
            "task_type": "search",
            "confidence": 0.85
        }
    """
    # Detect task type
    task_type = _detect_task_type(task)

    # Define preferences per task type
    preferences = {
        "search": ["ollama", "claude", "openai", "codex"],
        "explain": ["claude", "openai", "codex", "ollama"],
        "improve": ["codex", "openai", "claude", "ollama"],
        "review": ["claude", "openai", "codex", "ollama"],
        "generate": ["codex", "openai", "claude", "ollama"],
        "compare": ["claude", "openai", "codex", "ollama"],
        "general": ["ollama", "claude", "openai", "codex"]
    }

    # Get preference list for this task type
    preference_list = preferences.get(task_type, preferences["general"])

    # Task-specific reasoning
    task_reasons = {
        "search": "Task is a code search or lookup query. Ollama is fast and sufficient.",
        "explain": "Task requires explanation and reasoning. Claude has superior reasoning.",
        "improve": "Task requires code improvement. Codex is specialized for code generation.",
        "review": "Task requires code analysis. Claude is best at detailed analysis.",
        "generate": "Task requires code generation. Codex is best at this.",
        "compare": "Task requires comparison and analysis. Claude is best for this.",
        "general": "No specific task type detected. Ollama is a good default."
    }

    reason = task_reasons.get(task_type, task_reasons["general"])

    # Find best available agent
    recommended = None
    confidence = 0.0
    alternatives = []

    for i, agent in enumerate(preference_list):
        if agent in available:
            if recommended is None:
                recommended = agent
                # Confidence based on preference rank
                if i == 0:
                    confidence = 0.95  # Exact match
                elif i == 1:
                    confidence = 0.75  # First fallback
                elif i == 2:
                    confidence = 0.60  # Second fallback
                else:
                    confidence = 0.50  # Further fallback
            else:
                alternatives.append(agent)

    # Fallback if no match found
    if recommended is None:
        if available:
            recommended = available[0]
            confidence = 0.50
        else:
            recommended = "ollama"
            confidence = 0.0

    return {
        "recommended": recommended,
        "reason": reason,
        "alternatives": alternatives,
        "task_type": task_type,
        "confidence": round(confidence, 2)
    }

