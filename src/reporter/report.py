from __future__ import annotations

from datetime import datetime

from src.context.context_pack import assemble_context_pack
from src.agent.ollama_agent import query_agent


def generate_report(task: str, repo_path: str = ".") -> str:
    """
    Generate a comprehensive markdown report for a task.
    Returns a markdown string (does not write to file).
    """
    try:
        # Assemble context
        pack = assemble_context_pack(task=task, repo_path=repo_path)

        # Query agent for answer
        result = query_agent(task, repo_path)
        answer = result.get("answer", "")

        # Build markdown report
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        report = f"""# Context Engine Report

**Task:** {task}
**Generated:** {now}

## Relevant Code

"""

        chunks = pack.get("chunks", [])
        for chunk in chunks:
            name = chunk.get("chunk_name", "")
            file = chunk.get("file_path", "")
            score = chunk.get("score", 0.0)
            content = chunk.get("content", "")
            start = chunk.get("start_line", 0)
            end = chunk.get("end_line", 0)

            report += f"### {name} (in {file})\n\n"
            report += f"**Score:** {score:.2f} | **Lines:** {start}-{end}\n\n"
            report += f"```javascript\n{content}\n```\n\n"

        # Architecture Decisions
        report += "## Architecture Decisions\n\n"
        adrs = pack.get("adrs", [])
        if adrs:
            for adr in adrs:
                adr_id = adr.get("adr_id", "")
                title = adr.get("title", "")
                status = adr.get("status", "")
                decision = adr.get("decision", "")
                report += f"- **[{adr_id}] {title}** ({status})\n"
                report += f"  {decision}\n\n"
        else:
            report += "No ADRs found.\n\n"

        # Dependencies
        report += "## Dependencies\n\n"
        deps = pack.get("background", {}).get("dependencies", [])
        if deps:
            for dep in deps:
                imported = dep.get("imported_file", "")
                names = dep.get("imported_names", "")
                report += f"- `{imported}` — {names}\n"
        else:
            report += "No dependencies found.\n"
        report += "\n"

        # Git History
        report += "## Git History\n\n"
        commits = pack.get("git_history", [])
        if commits:
            for commit in commits:
                hash_str = commit.get("commit_hash", "")
                date = commit.get("date", "")
                author = commit.get("author_name", "")
                message = commit.get("message", "")
                report += f"- `{hash_str}` | {date} | {author} — {message}\n"
        else:
            report += "No git history found.\n"
        report += "\n"

        # Answer
        report += "## Answer\n\n"
        report += f"{answer}\n"

        return report
    except Exception as e:
        raise RuntimeError(f"Report generation failed: {e}")

