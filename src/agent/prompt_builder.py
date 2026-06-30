from __future__ import annotations


MERMAID_INSTRUCTION = (
    "\n\nWhen explaining flow, architecture, or relationships between files/functions, "
    "include a Mermaid diagram in a ```mermaid code block to illustrate it visually. "
    "Use 'graph TD' for flows/hierarchies and 'sequenceDiagram' for request/response interactions. "
    "Keep node labels short (2-4 words). Only include a diagram if it adds real clarity — "
    "skip it for simple answers."
)


def pick_instruction(task: str) -> str:
    """
    Choose a response style instruction based on what kind of question is being asked.
    Shared across all agents (Ollama, Groq, Claude, OpenAI, Codex) so every agent
    gets the same adaptive behavior instead of one generic instruction.
    """
    task_lower = task.lower()

    if any(word in task_lower for word in ['bug', 'issue', 'problem', 'wrong', 'fix', 'error']):
        return (
            "You are a senior engineer doing a code review. Based ONLY on the code above, "
            "point out real bugs or risks — only if they actually exist. If the code is genuinely fine, say so directly "
            "in one sentence instead of inventing minor nitpicks. Skip disclaimers like 'these are just observations.' "
            "Write like you're leaving comments in a pull request, not writing a report. "
            "Never start your response with 'Based on the provided code' or 'Based on the provided context.'"
        )
    elif any(word in task_lower for word in ['explain', 'what does', 'how does', 'understand']):
        return (
                "You are explaining this code to a teammate who's smart but unfamiliar with this specific file. "
                "Be conversational and direct — dive straight into what it does, no preamble. "
                "Trace the actual logic and flow in plain language, not a list of function names. "
                "If something genuinely isn't shown in the code provided, say what you'd need to see rather than guessing. "
                "Never start your response with 'Based on the provided code' or 'Based on the provided context.' "
                "Do not use bold section headers or a numbered summary at the end — write in flowing paragraphs. "
                "Keep paragraphs tight: a single newline between paragraphs, never a blank line or multiple line breaks."
                + MERMAID_INSTRUCTION
        )
    elif any(word in task_lower for word in ['connect', 'relate', 'depend', 'flow', 'architecture']):
        return (
                "Trace the actual data/control flow between these pieces of code like you're walking someone through "
                "a whiteboard diagram. Be specific about what calls what and why, not just a list of files. "
                "Never start your response with 'Based on the provided code' or 'Based on the provided context.' "
                "Keep paragraphs tight: a single newline between paragraphs, never a blank line or multiple line breaks."
                + MERMAID_INSTRUCTION
        )
    else:
        return (
            "Answer directly and specifically using the code above. Reference real function and variable names. "
            "Skip generic intros and disclaimers — get straight to the substance. "
            "Never start your response with 'Based on the provided code' or 'Based on the provided context.' "
            "Format lists as tight markdown bullets with NO blank line between items — each bullet should be a single line starting with '- ', immediately followed by the next bullet on the next line, no extra spacing."
        )