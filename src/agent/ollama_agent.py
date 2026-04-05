from __future__ import annotations
import os
from pathlib import Path
import httpx
from dotenv import load_dotenv
from src.context.context_pack import assemble_context_pack
from src.cache.query_cache import get_cached, store_cache  # ← this was missing

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "mistral")

def _make_prompt(pack: dict) -> str:
    p = f"TASK: {pack.get('task', '')}\n\n"
    p += "CODEBASE CONTEXT:\n=== DEPENDENCIES ===\n"
    for d in pack.get("background", {}).get("dependencies", []):
        p += f"  {d.get('imported_file')} imports {d.get('imported_names')}\n"
    p += "\n=== ARCHITECTURE ===\n"
    for a in pack.get("adrs", []):
        p += f"  [{a.get('adr_id')}] {a.get('title')}\n"
    p += "\n=== HISTORY ===\n"
    for c in pack.get("git_history", []):
        p += f"  {c.get('commit_hash')} {c.get('date')} {c.get('message')}\n"
    p += "\n=== CODE ===\n"
    for chunk in pack.get("chunks", []):
        p += f"  {chunk.get('chunk_name')} @ {chunk.get('file_path')}\n"
    p += "\n" + pack.get("instruction", "")
    return p

def query_agent(task: str, repo_path: str = ".") -> dict:
    # Check cache first
    cached_result = get_cached(task)
    if cached_result is not None:
        cached_result["cached"] = True
        return cached_result

    # Cache miss - run full pipeline
    pack = assemble_context_pack(task=task, repo_path=repo_path)
    prompt = _make_prompt(pack)
    client = httpx.Client(timeout=300.0)
    try:
        r = client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": CHAT_MODEL, "prompt": prompt, "stream": False}
        )
        r.raise_for_status()
        answer = r.json().get("response", "")
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}")
    finally:
        client.close()

    result = {
        "task": task,
        "answer": answer,
        "cached": False,
        "context_used": {
            "chunks": len(pack.get("chunks", [])),
            "adrs": len(pack.get("adrs", [])),
            "dependencies": len(pack.get("background", {}).get("dependencies", [])),
            "git_commits": len(pack.get("git_history", []))
        }
    }

    # Store in cache
    store_cache(task, result)

    return result