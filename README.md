# Context Engine

AI-native codebase context engine — semantic search, dependency graphs, ADRs, git history, and LLM answers, all from your local machine.

## What It Does

Context Engine transforms your codebase into an AI-searchable knowledge base. It chunks your code intelligently, embeds it into vectors, and lets you ask questions about your architecture. Get instant answers to "why is login failing?", "what does this function do?", or "show me authentication flow" — all without sending your code to the cloud.

Built for teams who want to understand their own codebases better. Works offline. No API keys required. Just Ollama + Qdrant running locally.

## Architecture

```
Files (JS, TS, Python, Java, Go, Rust, ...)
    ↓
Chunker (tree-sitter, ast, sliding-window)
    ↓
Embedder (nomic-embed-text via Ollama)
    ↓
Qdrant Vector DB
    ↓
    ├─→ Semantic Search + Re-ranking
    ├─→ Import Graph (SQLite)
    ├─→ ADRs (Architecture Decision Records)
    └─→ Git History (commits per file)
    ↓
Context Pack Assembler
    ↓
Ollama LLM (tinyllama / mistral)
    ↓
Answer → API / CLI / VS Code Extension / SSE Stream
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Chunker** | tree-sitter (JS/TS), ast (Python), sliding-window (others) |
| **Embeddings** | nomic-embed-text via Ollama |
| **Vector DB** | Qdrant |
| **LLM** | tinyllama / mistral via Ollama |
| **Backend** | FastAPI + uvicorn |
| **Database** | SQLite (graph, cache, auth, rate limits) |
| **VS Code** | WebviewPanel extension |
| **CLI** | argparse |
| **Languages** | JavaScript, TypeScript, Python, Java, Go, Rust, C++, C#, Ruby, PHP, Kotlin, Swift |

## Prerequisites

- **Python 3.13+**
- **Ollama** running locally (http://localhost:11434)
- **Qdrant** running locally (http://localhost:6333)
- **Node.js** (for VS Code extension only)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repo>
cd context-engine
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant:latest
```

### 4. Start Ollama

```bash
ollama serve
```

In another terminal, pull models:

```bash
ollama pull nomic-embed-text
ollama pull tinyllama
```

### 5. Configure Environment

```bash
cp .env.example .env
# Edit .env if needed (defaults point to localhost)
```

### 6. Index Your Codebase

```bash
export PYTHONPATH="."
python -m src.cli.cli index test-codebase
```

### 7. Start the API

```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

### 8. Try It Out

**CLI:**
```bash
python -m src.cli.cli search "login function"
python -m src.cli.cli ask "why is authentication failing"
```

**API:**
```bash
curl "http://localhost:8000/ask?task=what+does+login+do"
```

**VS Code:**
1. Open `vscode-extension/` folder
2. Press F5 to launch Extension Development Host
3. Run "Context Engine: Open Panel" command

## API Endpoints (19 Total)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check | ✗ |
| GET | `/health/full` | Full health status | ✗ |
| GET | `/search?query=<text>&top_k=5` | Semantic code search | ✓ |
| GET | `/context-pack?task=<text>` | Assemble context | ✓ |
| GET | `/ask?task=<text>` | Query AI agent | ✓ |
| GET | `/stream?task=<text>` | Stream response (SSE) | ✓ |
| GET | `/report?task=<text>` | Generate markdown report | ✓ |
| GET | `/graph/dependencies?file=<path>` | Get file imports | ✗ |
| GET | `/graph/dependents?file=<path>` | Get file dependents | ✗ |
| GET | `/adrs?file=<path>` | Get architecture decisions | ✗ |
| GET | `/cache/stats` | Cache statistics | ✗ |
| DELETE | `/cache` | Clear cache | ✗ |
| POST | `/watch` | Watch directory for changes | ✗ |
| GET | `/cli-help` | CLI command help | ✗ |
| POST | `/auth/keys` | Generate API key | ✗ |
| GET | `/auth/keys` | List API keys | ✗ |
| DELETE | `/auth/keys/{prefix}` | Revoke API key | ✗ |
| GET | `/auth/status` | Auth status | ✗ |
| GET | `/index?directory=<path>` | Index directory | ✓ |

## CLI Commands (14 Total)

| Command | Arguments | Description |
|---------|-----------|-------------|
| `index` | `<directory>` | Index a directory |
| `search` | `<query> [--top-k N]` | Semantic search |
| `ask` | `<task>` | Query AI agent |
| `health` | — | System health |
| `cache-stats` | — | Cache statistics |
| `cache-clear` | — | Clear cache |
| `deps` | `<file>` | File imports |
| `dependents` | `<file>` | File dependents |
| `adrs` | `<file>` | Architecture decisions |
| `git-log` | `<file>` | Git history |
| `chunk-stats` | `<directory>` | Chunking stats |
| `key-generate` | `<name>` | Generate API key |
| `key-list` | — | List API keys |
| `key-revoke` | `<prefix>` | Revoke API key |

## VS Code Extension

### Installation

```bash
# From VS Code:
1. Open vscode-extension/ folder
2. Press F5 or Run > Start Debugging
3. Opens Extension Development Host window
```

### Usage

In the Extension Dev Host:
- Press `Ctrl+Shift+P`
- Run "Context Engine: Open Panel"
- 4 tabs: Ask AI, Search, Health, Graph

### Features

- **Ask AI**: Real-time streaming responses with checkbox toggle
- **Search**: Semantic code search with expandable result cards
- **Health**: System health monitor with re-index button
- **Graph**: Dependency analysis and markdown report generation

## Project Structure

```
context-engine/
├── src/
│   ├── chunker/              # Code chunking (JS/TS, Python, others)
│   │   ├── chunker.py
│   │   ├── python_chunker.py
│   │   ├── generic_chunker.py
│   │   └── chunk_stats.py
│   ├── embedder/             # Ollama embeddings
│   │   └── embedder.py
│   ├── storage/              # Qdrant vector storage
│   │   └── qdrant_store.py
│   ├── search/               # Semantic search
│   │   ├── searcher.py
│   │   └── test_search.py
│   ├── indexer.py            # Pipeline: chunk → embed → store
│   ├── graph/                # Dependency graph
│   │   └── import_resolver.py
│   ├── context/              # Context assembly
│   │   ├── adr_store.py
│   │   ├── git_log.py
│   │   └── context_pack.py
│   ├── agent/                # LLM agents
│   │   ├── ollama_agent.py
│   │   ├── streaming_agent.py
│   │   └── watcher.py
│   ├── health/               # Health checking
│   │   └── checker.py
│   ├── cache/                # Query cache
│   │   └── query_cache.py
│   ├── reporter/             # Report generation
│   │   └── report.py
│   ├── cli/                  # CLI interface
│   │   ├── cli.py
│   │   └── __main__.py
│   ├── auth/                 # Authentication
│   │   ├── api_keys.py
│   │   ├── middleware.py
│   │   └── rate_limiter.py
│   └── api/                  # FastAPI backend
│       └── main.py
├── vscode-extension/         # VS Code extension
│   ├── extension.js
│   ├── media/panel.html
│   └── package.json
├── test-codebase/            # Sample code
│   ├── auth.js
│   ├── userRepository.js
│   ├── utils.js
│   └── sample.py
├── docs/adr/                 # Architecture Decision Records
├── .env                      # Configuration (git-ignored)
├── .env.example              # Configuration template
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker image
├── docker-compose.yml        # Full stack orchestration
├── verify_phase1.py          # Phase 1 tests
├── verify_phase2.py          # Phase 2 tests
│   ...
└── verify_phase10.py         # Phase 10 final tests
```

## Running Tests

Verify each phase completed successfully:

```bash
export PYTHONPATH="."

python verify_phase1.py
python verify_phase2.py
python verify_phase3.py
python verify_phase4.py
python verify_phase5.py
python verify_phase6.py
python verify_phase7.py
python verify_phase8.py
python verify_phase9.py
python verify_phase10.py
```

All phases: **10/10 expected**

## Authentication

By default, auth is disabled (development mode). To enable API key authentication:

1. Set `AUTH_ENABLED=true` in `.env`
2. Generate keys:
   ```bash
   python -m src.cli.cli key-generate my-app
   ```
3. Use key in requests:
   ```bash
   curl -H "X-API-Key: ce-a3f9b2c1d4e..." http://localhost:8000/ask?task=...
   ```

Rate limit: **60 requests per minute per key**

## Deployment

### Docker Compose (Recommended)

```bash
docker-compose up
```

Brings up all 3 services:
- **context-engine**: FastAPI backend (port 8000)
- **qdrant**: Vector DB (port 6333)
- **ollama**: LLM service (port 11434)

### Single Docker Container

Build just the backend:

```bash
docker build -t context-engine .
docker run -p 8000:8000 context-engine
```

Requires Qdrant and Ollama running separately.

## Environment Variables

See `.env.example`:

```
OLLAMA_URL=http://localhost:11434
QDRANT_URL=http://localhost:6333
COLLECTION_NAME=code_chunks
EMBED_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=tinyllama
AUTH_ENABLED=false
```

## Phase Completion

| Phase | Name | Status |
|-------|------|--------|
| 1 | Code Chunking & Search | ✅ |
| 2 | Code Understanding | ✅ |
| 3 | AI Integration | ✅ |
| 4 | Production Hardening | ✅ |
| 5 | CLI + Developer Tools | ✅ |
| 6 | VS Code Extension | ✅ |
| 7 | Multi-Language Support | ✅ |
| 8 | Real-Time Streaming | ✅ |
| 9 | Authentication + Multi-User | ✅ |
| 10 | Final Polish + Deployment | ✅ |

## License

Open source. Use freely.

## Support

Run `python -m src.cli.cli --help` for CLI help.
Check logs with `python -m src.cli.cli health`.
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

