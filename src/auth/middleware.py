from __future__ import annotations

import os
from pathlib import Path

from fastapi import Request, HTTPException
from dotenv import load_dotenv

from src.auth.api_keys import verify_api_key

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"


def require_auth(request: Request) -> None:
    """
    FastAPI dependency that enforces API key authentication.
    If AUTH_ENABLED is false, this passes all requests through.
    If AUTH_ENABLED is true, requires valid X-API-Key header.
    """
    if not AUTH_ENABLED:
        return None

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Pass key in X-API-Key header."
        )

    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Pass key in X-API-Key header."
        )

    return None

