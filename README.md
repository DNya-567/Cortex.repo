# Context Engine (Phase 1)

This phase extracts code chunks, embeds them with Ollama, and stores them in Qdrant.

## Components

- `src/chunker/chunker.py`: parses JS/TS files and returns `CodeChunk` records.
- `src/embedder/embedder.py`: calls Ollama `/api/embeddings` using `nomic-embed-text`.
- `src/storage/qdrant_store.py`: creates/upserts into Qdrant collection `code_chunks`.
- `src/indexer.py`: runs chunk -> embed -> store pipeline.
- `src/indexer_test.py`: indexes `test-codebase` and validates stored records.

## Environment

Create `.env` in project root:

```env
OLLAMA_URL=http://localhost:11434
QDRANT_URL=http://localhost:6333
COLLECTION_NAME=code_chunks
EMBED_MODEL=nomic-embed-text
```

## Run

```powershell
.\venv\Scripts\python.exe .\src\indexer_test.py
```

