from src.github.github_client import gh_get, gh_get_raw
from datetime import datetime


def _infer_language(path: str) -> str:
    """Infer programming language from file extension."""
    ext = path.lower().split('.')[-1] if '.' in path else ''

    mapping = {
        'js': 'javascript',
        'jsx': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'py': 'python',
        'java': 'java',
        'go': 'go',
        'rs': 'rust',
        'md': 'markdown',
        'json': 'json',
        'yml': 'yaml',
        'yaml': 'yaml',
        'css': 'css',
        'scss': 'css',
        'html': 'html',
    }
    return mapping.get(ext, 'unknown')


def get_repo_info(owner: str, repo: str) -> dict:
    """
    Get repository metadata from GitHub.

    Args:
        owner: GitHub username
        repo: Repository name

    Returns:
        Repository info dict with name, description, stars, etc.
    """
    try:
        data = gh_get(f"repos/{owner}/{repo}")
        return {
            "name": data.get("name", ""),
            "full_name": data.get("full_name", ""),
            "description": data.get("description", ""),
            "default_branch": data.get("default_branch", "main"),
            "language": data.get("language", ""),
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "created_at": data.get("created_at", ""),
            "updated_at": data.get("updated_at", ""),
            "topics": data.get("topics", []),
            "visibility": data.get("visibility", ""),
        }
    except Exception as e:
        raise RuntimeError(f"Failed to get repo info for {owner}/{repo}: {e}")


def get_file_tree(owner: str, repo: str,
                  branch: str = "main",
                  path: str = "") -> list[dict]:
    """
    Get flat list of files and directories in a path.

    Args:
        owner: GitHub username
        repo: Repository name
        branch: Branch name (default: main)
        path: Directory path (empty string for root)

    Returns:
        List of file/dir dicts sorted (dirs first, then files, both alphabetical)
    """
    try:
        api_path = f"repos/{owner}/{repo}/contents/{path}"
        data = gh_get(api_path)

        if not isinstance(data, list):
            data = [data]

        result = []
        for item in data:
            result.append({
                "name": item.get("name", ""),
                "path": item.get("path", ""),
                "type": item.get("type", ""),
                "size": item.get("size", 0),
                "download_url": item.get("download_url", ""),
            })

        # Sort: dirs first, then files, both alphabetical
        dirs = sorted([r for r in result if r["type"] == "dir"], key=lambda x: x["name"])
        files = sorted([r for r in result if r["type"] == "file"], key=lambda x: x["name"])

        return dirs + files
    except Exception as e:
        raise RuntimeError(f"Failed to get file tree for {owner}/{repo}/{path}: {e}")


def get_file_tree_recursive(owner: str, repo: str,
                            branch: str = "main",
                            path: str = "",
                            max_depth: int = 3) -> list[dict]:
    """
    Get recursive file tree up to max_depth levels.

    Args:
        owner: GitHub username
        repo: Repository name
        branch: Branch name (default: main)
        path: Starting path (empty string for root)
        max_depth: Maximum recursion depth

    Returns:
        Flat list of all files/dirs with depth field
    """
    skip_dirs = {"node_modules", ".git", "dist", "build", "__pycache__",
                 ".next", "coverage", ".nyc_output"}

    def _recurse(current_path: str, current_depth: int) -> list[dict]:
        if current_depth > max_depth:
            return []

        try:
            items = get_file_tree(owner, repo, branch, current_path)
            result = []

            for item in items:
                item["depth"] = current_depth
                result.append(item)

                # Recurse into directories
                if item["type"] == "dir" and item["name"] not in skip_dirs:
                    subpath = f"{current_path}/{item['name']}" if current_path else item['name']
                    result.extend(_recurse(subpath, current_depth + 1))

            return result
        except Exception:
            return []

    return _recurse(path, 0)


def get_file_content(owner: str, repo: str,
                     path: str,
                     branch: str = "main") -> dict:
    """
    Get content of a single file from GitHub.

    Args:
        owner: GitHub username
        repo: Repository name
        path: File path in repo
        branch: Branch name (default: main)

    Returns:
        Dict with path, content, lines, size_chars, language
    """
    try:
        content = gh_get_raw(owner, repo, path, branch)
        lines = len(content.split('\n'))

        return {
            "path": path,
            "content": content,
            "lines": lines,
            "size_chars": len(content),
            "language": _infer_language(path),
        }
    except Exception as e:
        raise RuntimeError(f"Failed to get file content for {owner}/{repo}/{path}: {e}")


def get_multiple_files(owner: str, repo: str,
                       paths: list[str],
                       branch: str = "main") -> list[dict]:
    """
    Get content of multiple files, skipping ones that fail.

    Args:
        owner: GitHub username
        repo: Repository name
        paths: List of file paths
        branch: Branch name (default: main)

    Returns:
        List of successful file content dicts
    """
    results = []
    for path in paths:
        try:
            result = get_file_content(owner, repo, path, branch)
            results.append(result)
        except Exception as e:
            print(f"WARNING: Failed to read {path}: {e}")

    return results

