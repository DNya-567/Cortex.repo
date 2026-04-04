# Context Engine (Phase 1)

This phase extracts code chunks, embeds them with Ollama, and stores them in Qdrant.

## Components

- `src/chunker/chunker.py`: parses JS/TS files and returns `CodeChunk` records.
- `src/embedder/embedder.py`: calls Ollama `/api/embeddings` using `nomic-embed-text`.
- `src/storage/qdrant_store.py`: creates/upserts into Qdrant collection `code_chunks`.
- `src/indexer.py`: runs chunk -> embed -> store pipeline.
- `src/indexer_test.py`: indexes `test-codebase` and validates stored records.
- `src/search/searcher.py`: converts a natural-language query into an embedding and searches Qdrant.
- `src/search/test_search.py`: runs 3 sample search queries without starting the API.
- `src/api/main.py`: FastAPI app with `/health` and `/search` endpoints.

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

## Search Test (No HTTP)

```powershell
.\venv\Scripts\python.exe .\src\search\test_search.py
```

## Run API

```powershell
.\venv\Scripts\python.exe -m uvicorn api.main:app --app-dir .\src --host 0.0.0.0 --port 8000
```

## API Example

```powershell
Invoke-RestMethod "http://localhost:8000/health"
Invoke-RestMethod "http://localhost:8000/search?query=where%20is%20user%20login%20handled&top_k=5"
```
