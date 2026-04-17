from src.github.github_client import gh_get


def list_pull_requests(owner: str, repo: str,
                       state: str = "open",
                       limit: int = 10) -> list[dict]:
    """
    List pull requests for a repository.

    Args:
        owner: GitHub username
        repo: Repository name
        state: PR state (open, closed, all)
        limit: Maximum number of PRs to return

    Returns:
        List of PR dicts with number, title, state, author, etc.
    """
    try:
        data = gh_get(f"repos/{owner}/{repo}/pulls?state={state}&per_page={limit}")

        if not isinstance(data, list):
            data = [data]

        result = []
        for pr in data:
            result.append({
                "number": pr.get("number", 0),
                "title": pr.get("title", ""),
                "state": pr.get("state", ""),
                "author": pr.get("user", {}).get("login", ""),
                "created_at": pr.get("created_at", "")[:10],  # YYYY-MM-DD
                "updated_at": pr.get("updated_at", "")[:10],
                "body": pr.get("body", ""),
                "branch": pr.get("head", {}).get("ref", ""),
                "base": pr.get("base", {}).get("ref", ""),
                "changed_files": pr.get("changed_files", 0),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
            })

        return result
    except Exception as e:
        raise RuntimeError(f"Failed to list PRs for {owner}/{repo}: {e}")


def get_pr_diff(owner: str, repo: str,
                pr_number: int) -> str:
    """
    Get formatted diff for a PR.

    Args:
        owner: GitHub username
        repo: Repository name
        pr_number: PR number

    Returns:
        Formatted diff string
    """
    try:
        data = gh_get(f"repos/{owner}/{repo}/pulls/{pr_number}/files")

        if not isinstance(data, list):
            data = [data]

        diff_lines = []
        for file_info in data:
            filename = file_info.get("filename", "")
            additions = file_info.get("additions", 0)
            deletions = file_info.get("deletions", 0)
            patch = file_info.get("patch", "")

            diff_lines.append(f"=== {filename} (+{additions} -{deletions}) ===")
            diff_lines.append(patch)
            diff_lines.append("")

        return "\n".join(diff_lines)
    except Exception as e:
        raise RuntimeError(f"Failed to get PR diff for #{pr_number}: {e}")


def get_pr_summary(owner: str, repo: str,
                   pr_number: int) -> dict:
    """
    Get full PR summary including metadata and diff.

    Args:
        owner: GitHub username
        repo: Repository name
        pr_number: PR number

    Returns:
        PR summary dict with metadata, files_changed, and diff_summary
    """
    try:
        # Get PR metadata
        pr_data = gh_get(f"repos/{owner}/{repo}/pulls/{pr_number}")

        pr_dict = {
            "number": pr_data.get("number", 0),
            "title": pr_data.get("title", ""),
            "state": pr_data.get("state", ""),
            "author": pr_data.get("user", {}).get("login", ""),
            "created_at": pr_data.get("created_at", "")[:10],
            "updated_at": pr_data.get("updated_at", "")[:10],
            "body": pr_data.get("body", ""),
            "branch": pr_data.get("head", {}).get("ref", ""),
            "base": pr_data.get("base", {}).get("ref", ""),
            "changed_files": pr_data.get("changed_files", 0),
            "additions": pr_data.get("additions", 0),
            "deletions": pr_data.get("deletions", 0),
        }

        # Get file changes
        files_data = gh_get(f"repos/{owner}/{repo}/pulls/{pr_number}/files")

        if not isinstance(files_data, list):
            files_data = [files_data]

        files_changed = []
        for file_info in files_data:
            files_changed.append({
                "filename": file_info.get("filename", ""),
                "additions": file_info.get("additions", 0),
                "deletions": file_info.get("deletions", 0),
                "patch": file_info.get("patch", ""),
            })

        diff_summary = f"{len(files_changed)} files: +{pr_dict['additions']} -{pr_dict['deletions']}"

        return {
            "pr": pr_dict,
            "files_changed": files_changed,
            "diff_summary": diff_summary,
        }
    except Exception as e:
        raise RuntimeError(f"Failed to get PR summary for #{pr_number}: {e}")

