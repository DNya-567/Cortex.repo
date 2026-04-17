# Phase 13 - Agent Comparison & Recommendation

**Date**: 2026-04-17  
**Status**: ✅ COMPLETE  
**Tests**: 12/12 PASSING

## Overview

Phase 13 adds **side-by-side agent comparison** and **intelligent agent recommendation** to the Context Engine. Users can now:

1. **Compare agents** - Run the same task on multiple LLMs simultaneously and see results side-by-side
2. **Get recommendations** - Receive AI-powered suggestions on which agent is best for a task
3. **Advanced scoring** - Agents are scored based on answer quality metrics
4. **Full UI integration** - New "Compare" tab in dashboard with agent selection and results visualization

## Files Created

### Core Modules

#### `src/orchestrator/comparator.py`
- **Purpose**: Run same task on multiple agents, compare results
- **Key Functions**:
  - `score_answer(answer: str) -> float` - Score answer 0.0-1.0 based on:
    - Length (max 500 chars) - 40%
    - Code blocks (```) - 20%
    - Lists/bullets - 20%
    - Specific identifiers - 10%
    - No errors - 10%
  - `compare_agents(task, agents, repo_path) -> dict` - Compare multiple agents
    - Runs each agent with same prompt
    - Scores each response
    - Returns best agent, comparison summary
    - Best agent: highest score, ties broken by preference (claude > openai > codex > ollama)

#### `src/orchestrator/selector.py`
- **Purpose**: Recommend best agent for a task based on type
- **Key Functions**:
  - `recommend_agent(task, available) -> dict` - Get recommendation
    - Detects task type: search, explain, improve, review, generate, compare, general
    - Routes to best agent:
      - Search → ollama (fast)
      - Explain → claude (reasoning)
      - Improve → codex (code generation)
      - Review → claude (analysis)
      - Generate → codex (code generation)
      - Compare → claude (reasoning)
      - General → ollama (default)
    - Returns recommendation with confidence score (0.50 - 0.95)
    - Confidence based on how good the match is

### API Endpoints (2 new)

#### `GET /recommend?task=<text>`
- **Purpose**: Get agent recommendation for a task
- **Response**:
  ```json
  {
    "recommended": "claude",
    "reason": "Task requires explanation and reasoning...",
    "alternatives": ["openai", "ollama"],
    "task_type": "explain",
    "confidence": 0.95
  }
  ```

#### `GET /compare?task=<text>&agents=<list>`
- **Purpose**: Compare multiple agents on same task
- **Response**:
  ```json
  {
    "task": "...",
    "results": [
      {
        "agent": "ollama",
        "answer": "...",
        "duration_ms": 1200,
        "tokens_used": 0,
        "error": null,
        "score": 0.85
      },
      {
        "agent": "claude",
        "answer": "...",
        "duration_ms": 800,
        "tokens_used": 342,
        "error": null,
        "score": 0.92
      }
    ],
    "best_agent": "claude",
    "comparison_summary": "claude answered in 800ms with higher detail..."
  }
  ```
- If `agents` param omitted: uses all available agents
- Agent parameter is comma-separated: `agents=ollama,claude,openai`

### User Interface

#### `dashboard_phase13.html` (New)
**Complete redesign with 7 main tabs:**

1. **Ask AI** - Single agent query with agent dropdown
   - Can select "Auto" (recommendation), ollama, claude, openai, or codex
   - Shows answer with metadata

2. **Search** - Semantic search across code
   - Shows top results with scores and snippets

3. **Compare** (NEW - Phase 13 flagship)
   - **Sub-tab 1: Compare Agents**
     - Textarea for task
     - Checkboxes for each available agent
     - "Compare Selected" and "Compare All" buttons
     - Results in side-by-side cards:
       - Gold border for best agent
       - Score bar (0-100%)
       - Duration in ms
       - Full answer text
   - **Sub-tab 2: Get Recommendation**
     - Task input
     - Shows recommendation card with:
       - Task type detected
       - Best agent with confidence %
       - Explanation of why
       - Alternative agents

4. **Orchestrate** (Enhanced with 3 sub-tabs)
   - **Single Agent**: Select agent from visual cards, run task
   - **Compare Agents**: Compare all agents' responses
   - **Multi-Agent**: Full orchestration pipeline with mode selector

5. **Health** - System status check

6. **Graph** - Code dependencies and ADRs

7. **GitHub** - GitHub repo exploration and indexing

**Agent Status Bar** (New - Top of page)
- Shows available agents with green dots: ● ollama  ● claude  ○ openai  ○ codex
- Real-time status from `/orchestrate/agents` endpoint

## How It Works

### Workflow 1: Compare Agents
```
User: "What does login do?"
   ↓
Frontend: Get available agents
   ↓
User selects: ollama, claude
   ↓
POST /compare?task=...&agents=ollama,claude
   ↓
Backend: 
  1. Assemble context pack once
  2. Run task on ollama → score 0.85
  3. Run task on claude → score 0.92
  4. Determine best: claude
   ↓
Response: [ollama result, claude result] + best_agent + summary
   ↓
Dashboard: Show side-by-side with gold highlight on best
```

### Workflow 2: Get Recommendation
```
User: "Explain the authentication flow"
   ↓
GET /recommend?task=...
   ↓
Backend:
  1. Detect task type: "explain"
  2. Route to best agent: claude
  3. Get available agents
  4. Return recommendation with alternatives
   ↓
Response: {recommended: "claude", confidence: 0.95, ...}
   ↓
Dashboard: Show recommendation card with explanation
```

### Scoring Heuristic
```
score = 0.0

// Length (0-0.4)
score += min(len(answer)/500, 1.0) * 0.4

// Has code blocks (0-0.2)
if "```" in answer: score += 0.2

// Has lists (0-0.2)
if has bullets or numbers: score += 0.2

// Has specific references (0-0.1)
if has file/function names: score += 0.1

// No errors (0-0.1)
if no "error"/"failed": score += 0.1

return round(min(score, 1.0), 2)
```

## API Integration

### New Endpoints in src/api/main.py
```python
@app.get("/recommend")
def recommend_endpoint(task: str) -> dict:
    from src.orchestrator.selector import recommend_agent
    available = get_available_agents()
    return recommend_agent(task, available)

@app.get("/compare")
def compare_endpoint(task: str, agents: str = None) -> dict:
    from src.orchestrator.comparator import compare_agents
    agent_list = agents.split(",") if agents else get_available_agents()
    return compare_agents(task, agent_list, ".")
```

## Testing

All 12 tests pass:

| # | Test | Result |
|---|------|--------|
| 1 | Comparator imports | ✅ |
| 2 | Score answer function | ✅ |
| 3 | Compare agents (single) | ✅ |
| 4 | Selector imports | ✅ |
| 5 | Recommend agent | ✅ |
| 6 | API /recommend endpoint | ✅ |
| 7 | API /compare (single agent) | ✅ |
| 8 | API /compare (no agents param) | ✅ |
| 9 | Dashboard comparison UI | ✅ |
| 10 | Dashboard agent status bar | ✅ |
| 11 | Dashboard sub-tabs | ✅ |
| 12 | Full pipeline | ✅ |

Run tests:
```bash
$env:PYTHONPATH="."; venv\Scripts\python.exe verify_phase13.py
```

## Import Rule Compliance

✅ All internal imports use `src.` prefix:
- `from src.orchestrator.comparator import compare_agents`
- `from src.orchestrator.selector import recommend_agent`
- `from src.context.context_pack import assemble_context_pack`
- `from src.orchestrator.agents import run_agent, get_available_agents`

✅ No async/await - fully synchronous

✅ No new pip dependencies - uses only existing packages

## System Architecture Update

```
                Input
                  ↓
    ┌─────────────┴─────────────┐
    ↓                           ↓
  Search                   Recommendation
    ↓                           ↓
Context Pack              Task Type Detector
    ↓                           ↓
    ├─────────→ Single LLM Query ←─────────┐
    │                   ↓                   │
    │           ┌───────┴────────┐          │
    │           ↓                ↓          │
    │       Agent 1          Agent 2    Selector
    │           ↓                ↓          ↓
    │        Score 0.85    Score 0.92   Suggest
    │           ↓                ↓          ↓
    └──────→ Compare Results ←──┴──────────┘
                    ↓
            Best Agent: claude
            Confidence: 95%
                    ↓
              Recommendation
          or Side-by-side UI
```

## Usage Examples

### Command Line (CLI)
```bash
# Get recommendation for task
python -m src.cli.cli recommend "fix the authentication bug"
# → Task type: improve
#   Recommended: codex (95% confidence)

# Single agent query
python -m src.cli.cli ask "what does login do"
# → Uses recommended agent automatically

# Multi-agent comparison (if added to CLI)
python -m src.cli.cli compare-agents "explain auth flow"
# → Runs on ollama, claude, openai, codex
#   Shows side-by-side results
```

### REST API
```bash
# Get recommendation
curl "http://localhost:8000/recommend?task=fix+login+bug"
# → {"recommended":"codex","task_type":"improve","confidence":0.95}

# Compare 2 agents
curl "http://localhost:8000/compare?task=what+does+login+do&agents=ollama,claude"
# → {results: [{agent:"ollama",score:0.85,...}, {agent:"claude",score:0.92,...}], best_agent:"claude"}

# Compare all available agents (default)
curl "http://localhost:8000/compare?task=explain+auth"
# → Uses all agents returned by /orchestrate/agents
```

### Dashboard
1. Open `dashboard_phase13.html` in browser
2. Agent status bar shows available agents
3. Click "Compare" tab
4. Enter task, select agents, click "Compare All"
5. See side-by-side results with scores and best highlighted
6. Or use "Get Recommendation" sub-tab to see AI suggestion

## Phase 13 Deliverables

✅ `src/orchestrator/comparator.py` - Compare multiple agents  
✅ `src/orchestrator/selector.py` - Recommend best agent  
✅ Updated `src/api/main.py` - 2 new endpoints  
✅ `dashboard_phase13.html` - Full UI redesign  
✅ `verify_phase13.py` - 12 passing tests  
✅ This documentation

## Next Phase (Phase 14+)

Potential enhancements:
- Agent ensemble (combine best answers)
- Custom agent weights/priorities
- Agent performance history and learning
- Fine-tuned embeddings per agent type
- Distributed agent execution
- Agent feedback loops
- Cost/speed optimization
- Advanced routing heuristics

---

**Phase 13 Status**: ✅ **COMPLETE**  
**All Tests Passing**: ✅ **12/12**  
**Production Ready**: ✅ **YES**


