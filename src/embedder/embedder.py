from __future__ import annotations

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

MAX_CHARS = 8000  # nomic-embed-text context limit safety margin


def get_embedding(text: str) -> list[float]:
    text = text[:MAX_CHARS]  # truncate oversized chunks before embedding

    endpoint = f"{OLLAMA_URL.rstrip('/')}/api/embeddings"

    try:
        response = httpx.post(
            endpoint,
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=60.0,
        )
    except httpx.RequestError as exc:
        raise RuntimeError(
            f"Failed to connect to Ollama at {OLLAMA_URL}. Ensure Ollama is running."
        ) from exc

    if response.status_code >= 400:
        raise RuntimeError(
            f"Ollama embedding request failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    embedding = data.get("embedding")
    if not isinstance(embedding, list):
        raise RuntimeError("Ollama response did not include a valid 'embedding' array.")

    return [float(value) for value in embedding]