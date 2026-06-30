from __future__ import annotations
import hashlib
import json
from pathlib import Path

MANIFEST_DIR = Path(__file__).resolve().parents[2] / ".manifests"
MANIFEST_DIR.mkdir(exist_ok=True)


def _manifest_path(collection_name: str) -> Path:
    return MANIFEST_DIR / f"{collection_name}.json"


def load_manifest(collection_name: str) -> dict[str, str]:
    """Load the saved file_path -> content_hash map for this project. Empty if none exists."""
    path = _manifest_path(collection_name)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_manifest(collection_name: str, manifest: dict[str, str]) -> None:
    """Save the file_path -> content_hash map for this project."""
    path = _manifest_path(collection_name)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def hash_content(content: str) -> str:
    """Deterministic hash of file content, used to detect changes."""
    return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()