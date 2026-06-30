"""Unified interface for multiple AI agents (Ollama, Claude, OpenAI, Groq, OpenRouter, Codex)."""

import httpx
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


def get_available_agents() -> list[str]:
    """
    Returns list of agents that have valid credentials.
    Always includes 'ollama' if reachable.
    """
    available = []

    # Check Ollama
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(OLLAMA_URL)
            if r.status_code == 200:
                available.append("ollama")
    except Exception:
        pass

    # Check Claude
    if ANTHROPIC_API_KEY:
        available.append("claude")

    # Check OpenAI
    if OPENAI_API_KEY:
        available.append("openai")
        available.append("codex")

    # Check Groq
    if GROQ_API_KEY:
        available.append("groq")

    # Check OpenRouter
    if OPENROUTER_API_KEY:
        available.append("openrouter")

    return available


def run_agent(agent: str, prompt: str, max_tokens: int = 1000) -> dict:
    """
    Runs the specified agent with the prompt.
    Returns dict with: agent, answer, tokens_used, duration_ms, error
    """
    start_time = time.time()

    if agent == "ollama":
        result = _run_ollama(prompt, max_tokens)
    elif agent == "claude":
        result = _run_claude(prompt, max_tokens)
    elif agent == "openai":
        result = _run_openai(prompt, max_tokens)
    elif agent == "codex":
        result = _run_codex(prompt, max_tokens)
    elif agent == "groq":
        result = _run_groq(prompt, max_tokens)
    elif agent == "openrouter":
        result = _run_openrouter(prompt, max_tokens)
    else:
        result = {
            "agent": agent,
            "answer": "",
            "tokens_used": 0,
            "duration_ms": 0,
            "error": f"Unknown agent: {agent}",
        }

    # Add duration if not already set
    if "duration_ms" not in result or result["duration_ms"] == 0:
        result["duration_ms"] = int((time.time() - start_time) * 1000)

    return result


def _run_ollama(prompt: str, max_tokens: int) -> dict:
    """Run Ollama model."""
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_CHAT_MODEL,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            answer = data.get("response", "").strip()
            return {
                "agent": "ollama",
                "answer": answer,
                "tokens_used": 0,
                "duration_ms": 0,
                "error": None,
            }
    except Exception as e:
        return {
            "agent": "ollama",
            "answer": "",
            "tokens_used": 0,
            "duration_ms": 0,
            "error": str(e),
        }


def _run_claude(prompt: str, max_tokens: int) -> dict:
    """Run Claude model via Anthropic API."""
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-5-haiku-20241022",
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            answer = data["content"][0]["text"]
            tokens_used = data.get("usage", {}).get("input_tokens", 0) + data.get(
                "usage", {}
            ).get("output_tokens", 0)
            return {
                "agent": "claude",
                "answer": answer,
                "tokens_used": tokens_used,
                "duration_ms": 0,
                "error": None,
            }
    except Exception as e:
        return {
            "agent": "claude",
            "answer": "",
            "tokens_used": 0,
            "duration_ms": 0,
            "error": str(e),
        }


def _run_openai(
    prompt: str, max_tokens: int, system: str = None
) -> dict:
    """Run OpenAI model via OpenAI API."""
    try:
        if system is None:
            system = "You are a helpful assistant."

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "max_tokens": max_tokens,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            return {
                "agent": "openai",
                "answer": answer,
                "tokens_used": tokens_used,
                "duration_ms": 0,
                "error": None,
            }
    except Exception as e:
        return {
            "agent": "openai",
            "answer": "",
            "tokens_used": 0,
            "duration_ms": 0,
            "error": str(e),
        }


def _run_codex(prompt: str, max_tokens: int) -> dict:
    """Run Codex (OpenAI with code-focused system prompt)."""
    system = """You are an expert software engineer. Analyze code carefully
and provide precise, technical answers. Focus on implementation details,
patterns, and potential issues."""
    return _run_openai(prompt, max_tokens, system=system)


def _run_groq(prompt: str, max_tokens: int) -> dict:
    """Run Groq model via Groq API (OpenAI-compatible format)."""
    try:
        if not GROQ_API_KEY:
            return {
                "agent": "groq",
                "answer": "",
                "tokens_used": 0,
                "duration_ms": 0,
                "error": "API key not configured",
            }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": "llama-3.1-8b-instant",
                    "max_tokens": max_tokens,
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            return {
                "agent": "groq",
                "answer": answer,
                "tokens_used": tokens_used,
                "duration_ms": 0,
                "error": None,
            }
    except Exception as e:
        return {
            "agent": "groq",
            "answer": "",
            "tokens_used": 0,
            "duration_ms": 0,
            "error": str(e),
        }


def _run_openrouter(prompt: str, max_tokens: int) -> dict:
    """Run OpenRouter model via OpenRouter API (OpenAI-compatible format)."""
    try:
        if not OPENROUTER_API_KEY:
            return {
                "agent": "openrouter",
                "answer": "",
                "tokens_used": 0,
                "duration_ms": 0,
                "error": "API key not configured",
            }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Context Engine",
                },
                json={
                    "model": "openrouter/free",
                    "max_tokens": max(max_tokens, 2000),
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            message = data["choices"][0]["message"]
            answer = message.get("content") or message.get("reasoning") or ""
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            return {
                "agent": "openrouter",
                "answer": answer,
                "tokens_used": tokens_used,
                "duration_ms": 0,
                "error": None,
            }
    except Exception as e:
        return {
            "agent": "openrouter",
            "answer": "",
            "tokens_used": 0,
            "duration_ms": 0,
            "error": str(e),
        }


