import os
import tempfile
from pathlib import Path

from src.github.repo import get_file_tree_recursive, get_file_content
from src.chunker.chunker import chunk_file_any
from src.embedder.embedder import get_embedding
from src.storage.qdrant_store import setup_collection, store_chunk, get_collection_name


def index_github_repo(owner: str, repo: str,
                      branch: str = "main",
                      path: str = "",
                      max_depth: int = 3) -> dict:
    """
    Index a GitHub repository directly into Qdrant.

    Args:
        owner: GitHub username
        repo: Repository name
        branch: Branch name (default: main)
        path: Starting path (empty string for root)
        max_depth: Maximum recursion depth

    Returns:
        Summary dict with total_files, total_chunks, skipped_files, status
    """
    collection_name = get_collection_name(f"github:{owner}/{repo}")
    setup_collection(collection_name)

    supported_exts = {".js", ".jsx", ".ts", ".tsx", ".py",
                     ".java", ".go", ".rs"}

    # Get all files from repo
    try:
        all_items = get_file_tree_recursive(owner, repo, branch, path, max_depth)
        files = [item for item in all_items if item["type"] == "file"]
    except Exception as e:
        raise RuntimeError(f"Failed to get repo tree: {e}")

    # Filter to supported code files
    code_files = [f for f in files
                  if Path(f["path"]).suffix.lower() in supported_exts]

    total_files = len(code_files)
    total_chunks = 0
    skipped_files = 0

    for file_item in code_files:
        try:
            # Get file content
            file_content = get_file_content(owner, repo, file_item["path"], branch)

            # Write to temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix=Path(file_item["path"]).suffix,
                delete=False
            ) as tmp:
                tmp.write(file_content["content"])
                tmp_path = tmp.name

            try:
                # Chunk the temp file
                chunks = chunk_file_any(tmp_path)

                # Store each chunk
                for chunk in chunks:
                    # Fix file path to use repo path instead of temp path
                    chunk.file_path = f"{owner}/{repo}/{file_item['path']}"
                    chunk.chunk_id = f"{chunk.file_path}::{chunk.chunk_name}::{chunk.start_line}"

                    # Get embedding and store
                    embedding = get_embedding(chunk.content)
                    store_chunk(chunk, embedding, collection_name)
                    total_chunks += 1

                print(f"[OK] {file_item['path']}: {len(chunks)} chunks")

            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        except Exception as e:
            print(f"[SKIP] {file_item['path']}: {e}")
            skipped_files += 1

    return {
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "total_files": total_files,
        "total_chunks": total_chunks,
        "skipped_files": skipped_files,
        "status": "ok",
    }

