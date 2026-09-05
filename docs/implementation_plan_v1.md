# End-to-End Upgrade Plan — AI Data Analyst Agent

Based on the System Change Proposal, Tokenization Notes, and the new IDE-style multi-chat workspace requirement. Every step is self-contained so the application remains functional end-to-end at every phase.

---

## Current Progress Overview

| Step   | Feature                         | Status       | Description                                                                                          |
|--------|---------------------------------|--------------|------------------------------------------------------------------------------------------------------|
| Step 1 | Token Display Persistence       | Completed    | localStorage persistence, daily midnight auto-reset, provider breakdown (Groq / Gemini) with dots.   |
| Step 2 | ToolRegistry Schemas            | Completed    | 7 structured tools registered in ToolRegistry with Gemini-compatible function schemas.               |
| Step 3 | Multi-Chat & Dataset Scoping    | Completed    | IDE-style isolated workspaces: SessionStore holds isolated df + history; + New Chat in sidebar.      |
| Step 4 | Wire Coordinator Execution      | Current Task | AgentCoordinator.process_query() executes tool loops against the session's isolated dataset.         |
| Step 5 | Router LLM Classification       | Planned      | Lightweight intent classification into Structured vs. RAG vs. Hybrid with heuristic fallback.        |
| Step 6 | RAG Layer (Unstructured Data)   | Planned      | Text chunking + vector embeddings + semantic retrieval for markdown/text knowledge docs.             |
| Step 7 | API Route Switchover            | Planned      | Connect /api/ask to AgentCoordinator behind a safety feature flag.                                   |
| Step 8 | File Upload UI & Polish         | Planned      | Drag-and-drop CSV and doc uploads, dataset management UI, and final hardening.                       |

---

## Detailed Step Specifications

### [Completed] Step 1 — Fix Token Display Persistence
- **Goal:** Token count persists across page refreshes and differentiates providers.
- **Implemented:**
  - `App.jsx`: `tokenUsage` initializes from and saves to `localStorage` (keyed by current date).
  - `TokenUsageDisplay.jsx`: Added per-provider breakdown (Gemini / Groq).
  - `Sidebar.jsx`: Threaded `activeModel` prop.
  - Verified: Refresh retains count; "Clear Chat" resets cleanly.

---

### [Completed] Step 2 — Register Structured Tools in ToolRegistry
- **Goal:** All structured tools discoverable via standard registry with function calling schemas.
- **Implemented:**
  - Created `registry_setup.py` with 7 tools registered: `get_dataset_schema`, `filter_rows`, `aggregate_data`, `group_data`, `sort_data`, `get_unique_values`, `generate_chart`.
  - Tools are completely data-agnostic; the `df` is injected at execution time rather than hardcoded.
  - Verified: `test_registry.py` confirms all 7 tools resolve and schemas validate.

---

### [Completed] Step 3 — Multi-Chat Sessions & Dataset Scoping
- **Goal:** Create isolated IDE-style chat workspaces ("voids"). Each chat session is permanently locked to its chosen dataset, with its own conversation history and token usage with zero cross-talk.
- **Implemented:**
  - `dataset_manager.py`: Discovers raw CSVs and caches DataFrames in memory.
  - `session_store.py`: Upgraded `SessionMemory` into `SessionStore` with isolated `ChatSession` workspaces.
  - `routes.py`: Added `/api/sessions`, `/api/datasets`, and `/api/upload` endpoints; `/api/ask` executes against session's private `df`.
  - `NewChatModal.jsx`: Modal triggered by `+ New Chat` allowing users to select either an existing dataset in storage or browse/open a `.csv` file directly from their computer explorer.
  - `Sidebar.jsx`: Added `+ New Chat` button, dynamic chat workspace list with dataset badges and delete buttons.
  - `Header.jsx`: Eliminated the upload button and dataset dropdown; replaced with a clean, read-only indicator badge showing the dataset currently locked to the active chat void.
  - `App.jsx`: Multi-session switching, history restoration, token isolation, and modal integration.
  - Verified: `test_sessions_backend.py` confirms Chat A (Netflix) and Chat B (Tech Salaries) run independently with zero cross-talk. All frontend builds pass cleanly.

---

### [Current Task] Step 4 — Wire Coordinator to Actually Execute Tools
- **Goal:** Transform `AgentCoordinator` from a skeleton into an active execution engine.
- **What will be built:**
  - `coordinator.py`:
    1. Look up session from `SessionStore` to get the session's isolated `df`.
    2. Obtain route classification from Router.
    3. For `"structured"`: Invoke LLM with tool schemas from `default_registry` -> parse tool calls -> execute tool functions against `session.df` -> return analysis result.
    4. For `"rag"`: Call `search_documents()`.
    5. For `"hybrid"`: Execute structured analysis + retrieve relevant documentation and synthesize a single answer.
    6. Record conversation turn and token usage into `SessionStore`.
  - `prompts.py`: Tool-calling system prompt and coordinator guidance.
- **Verification:** Direct test script invoking `coordinator.process_query(session_id, question)` on a session and receiving real computed results.

---

### [Planned] Step 5 — Upgrade Router to LLM Classification
- **Goal:** Intelligent intent routing that decides whether a query needs structured calculations, document lookup, or both.
- **What will be built:**
  - `router.py`:
    - Add `llm_route()` using a concise system prompt (`ROUTER_SYSTEM_PROMPT`) returning `{"route": "structured" | "rag" | "hybrid"}`.
    - Keep fast regex/keyword pattern matching as zero-cost fallback when offline or to conserve quota.
- **Verification:** Diverse query test suite verifying:
  - "Top 5 oldest movies" -> `structured`
  - "What does TV-MA mean?" -> `rag`
  - "List all TV-MA shows and explain why they received this rating" -> `hybrid`

---

### [Planned] Step 6 — Build RAG Layer (Embeddings + Vector Search)
- **Goal:** Enable the agent to answer questions from unstructured knowledge documents (markdown/text/data dictionaries).
- **What will be built:**
  - `indexer.py`: Document ingestion pipeline that scans `data/knowledge/`, chunks documents into ~300-token passages, and generates vector embeddings.
  - `retriever.py`: In-memory cosine similarity search over chunk vectors.
  - `rag_tools.py`: Connects `search_documents(query)` tool to the retriever and registers it in `default_registry`.
- **Verification:** Query `search_documents("content rating criteria")` returns relevant excerpts with similarity scores.

---

### [Planned] Step 7 — Switch API Route from Legacy to Agent Coordinator
- **Goal:** `/api/ask` serves answers via the modern `AgentCoordinator` pipeline instead of the legacy `query_planner.py`.
- **What will be built:**
  - `routes.py`:
    - Refactor `/api/ask` to call `coordinator.process_query()`.
    - Add safety feature flag `USE_LEGACY_AGENT=false` in `.env` so you can revert instantly if needed.
- **Verification:** Run the full frontend and ask complex queries; verify answers, token displays, and charts continue functioning without regression.

---

### [Planned] Step 8 — File Upload UI, Hardening & Polish
- **Goal:** Allow users to upload new CSV datasets and unstructured documents directly from the UI.
- **What will be built:**
  - `POST /api/upload`: Handles file uploads into `data/raw/` (for CSVs) and `data/knowledge/` (for text/markdown).
  - Frontend Upload Modal: Drag-and-drop file upload linked to the Header "Upload" button and "+ New Chat" flow.
  - Auto-trigger dynamic dataset description and RAG indexing upon upload.
  - Full end-to-end regression testing and cleanup of scratch scripts.
