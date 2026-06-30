import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
BASE_URL = "https://api.github.com"


def gh_get(path: str) -> dict | list:
    """
    GET request to GitHub API.

    Args:
        path: API path (without leading slash), e.g. "repos/octocat/Hello-World"

    Returns:
        JSON response as dict or list

    Raises:
        RuntimeError: if request fails
    """
    url = f"{BASE_URL}/{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        response = httpx.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise RuntimeError(f"GitHub API error: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {path}: {e}")


def gh_get_raw(owner: str, repo: str,
               path: str, branch: str = "main") -> str:
    """
    GET raw file content from GitHub.

    Args:
        owner: GitHub username
        repo: Repository name
        path: File path in repo
        branch: Branch name (default: main)

    Returns:
        Raw file content as string

    Raises:
        RuntimeError: if file not found or request fails
    """
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"

    try:
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        raise RuntimeError(f"Failed to fetch raw file {path}: {e}")
    except Exception as e:
        raise RuntimeError(f"Error reading {owner}/{repo}/{path}: {e}")

