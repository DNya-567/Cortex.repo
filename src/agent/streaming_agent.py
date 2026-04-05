from __future__ import annotations

import json
import os
from typing import Iterator

import httpx
from dotenv import load_dotenv
from pathlib import Path

from src.context.context_pack import assemble_context_pack
from src.agent.ollama_agent import _make_prompt

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "mistral")


def stream_agent(task: str, repo_path: str = ".") -> Iterator[str]:
    """
    Stream LLM response token by token from Ollama.
    Yields each token string as it arrives.
    """
    try:
        pack = assemble_context_pack(task=task, repo_path=repo_path)
        prompt = _make_prompt(pack)
    except Exception as e:
        raise RuntimeError(f"Failed to assemble context: {e}")

    client = httpx.Client(timeout=300.0)
    try:
        url = f"{OLLAMA_URL}/api/generate"
        body = {
            "model": CHAT_MODEL,
            "prompt": prompt,
            "stream": True,
        }

        with client.stream("POST", url, json=body) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    token = data.get("response", "")
                    done = data.get("done", False)

                    if token:
                        yield token

                    if done:
                        break
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        raise RuntimeError(f"Ollama streaming error: {e}")
    finally:
        client.close()

