# AI Data Analyst Agent

A full-stack AI agent that answers plain-English questions about a structured dataset, generates a safe query plan via an LLM, executes it against real data, and returns a plain-English summary plus a chart — no `eval()`, no raw AI-generated code execution.

Built as a portfolio project to demonstrate full-stack + AI integration skills, inspired by an AWS-based AI data analyst architecture but rebuilt on a fully free stack.

**GitHub:** https://github.com/ralphrowel/AI_Data_Analyst_Agent

---

## What it does

Ask a question like *"What is the total number of Movie and TV Show titles?"* or *"Show me all titles made in Japan"* and the agent will:

1. Turn your question into a structured JSON query plan (never raw executable code)
2. Safely execute that plan against the dataset with Pandas
3. Summarize the result in plain English
4. Generate a matching chart automatically (or let you pick the chart type yourself)

If a question can't be answered with the available data, the agent honestly says so (`unsupported`) instead of guessing.

---

## Tech stack

| Layer | Tech |
|---|---|
| LLM (primary) | Groq (`openai/gpt-oss-120b`) |
| LLM (fallback) | Groq free tier (`llama-3.3-70b-versatile`) — auto-switches when Gemini's daily quota is hit |
| Data | Pandas, NumPy |
| Charts | Matplotlib, returned as in-memory base64 (no disk I/O) |
| Backend | FastAPI + Uvicorn |
| Frontend | React (Vite) + Tailwind CSS v4 |
| Dataset | Netflix Titles (Kaggle), 8,807 rows / 12 columns |

---

## Core design decisions

- **Structured JSON over code execution** — the LLM returns a query plan (`filter`, `value_counts`, `group_by_agg`, `sort_limit`, or `unsupported`), never code, so nothing AI-generated is ever `eval()`'d against real data.
- **Honest refusals over fabrication** — `unsupported` is a valid, intentional response, not an error state.
- **Two-call pattern** — Call 1 turns the question into a query plan; Call 2 turns the results into a plain-English summary.
- **LLM fallback** � Groq is the configured default; Gemini is used when Groq fails and a Gemini key is available. When Gemini is selected, quota errors may fall back to Groq.
- **Charts travel as base64 in the JSON response** — generated in-memory via `io.BytesIO()`, never written to disk, so it works on read-only deployment filesystems (Render/Railway).

---

## Project structure

```
Ai Data Analyst Agent/
├── backend/                      # Modular backend package
│   ├── app/
│   │   ├── main.py               # FastAPI application & CORS
│   │   ├── config.py             # Centralized settings & data paths
│   │   ├── api/                  # REST endpoints & Pydantic schemas
│   │   │   ├── routes.py         # /api/ask, /api/suggestions
│   │   │   └── schemas.py
│   │   ├── agent/                # Router, Coordinator & Prompt orchestration
│   │   ├── tools/                # Controlled Data, RAG & Chart tools
│   │   │   ├── structured_tools.py
│   │   │   ├── rag_tools.py
│   │   │   └── chart_tool.py
│   │   ├── rag/                  # Document indexer & vector retriever
│   │   ├── memory/               # Multi-turn conversation state
│   │   ├── data_engine/          # Loader & Profiler modules
│   │   ├── llm/                  # Gemini & Groq fallback client
│   │   └── legacy/               # Archived single-shot query planner & executor
│   └── run_cli.py                # CLI runner harness
├── data/
│   ├── raw/                      # Tabular datasets (netflix_titles.csv)
│   └── knowledge/                # Unstructured documentation for RAG lookup
├── docs/                         # System proposals & technical notes
├── tests/                        # Tests and secondary datasets (sample_orders.csv)
├── frontend/                     # React (Vite) + Tailwind CSS
│   └── src/
│       ├── api.js                # Fetch calls to FastAPI
│       └── components/           # UI components
├── .env                          # API keys & environment config
├── api.py                        # Root backward-compatible server proxy
└── requirements.txt
```

---

## Running locally

```bash
# Backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn backend.app.main:app --reload   # (or: uvicorn api:app --reload)

# Frontend
cd frontend
npm install
npm run dev
```

Copy `.env.example` to `.env` and `frontend/.env.example` to `frontend/.env.local`.
Configure `DATABASE_URL` for PostgreSQL (Supabase Postgres is supported), Supabase auth, at least one LLM key, and allowed frontend origins. Run `python -m backend.app.storage` before starting the API to initialize the schema. Use a migration/admin database account for initialization and a restricted application account at runtime. The backend fails startup if the database or schema is unavailable.

Set `VITE_API_BASE_URL` to your backend URL before building. If omitted, requests use the frontend origin. Frontend variables are public: never put database credentials or JWT signing secrets in `VITE_*` variables.

All `/api/*` routes require a valid Supabase access token. Asymmetric tokens use the configured project's JWKS; legacy HS256 projects can set `SUPABASE_JWT_SECRET`. Both paths require issuer, audience, expiry, issued-at, subject, and authenticated role. Demo profiles require **both** backend `APP_ENV=development` / `ALLOW_DEMO_AUTH=true` and frontend development mode / `VITE_ALLOW_DEMO_AUTH=true`. No guest or unverified-token fallback exists.

Users, chat sessions (history/widgets/usage), daily quotas, activity, and dataset metadata live in the PostgreSQL `app_records` table. This is a backend-only table: do not grant browser/anon/authenticated roles direct access. CSV and knowledge content still live on disk; use a persistent shared volume across workers and back it up. Shared sample datasets are copied into the user's private directory when edited. Knowledge uploads and indexes are private to each user.

Existing `data/quotas.json` is no longer read. Previously in-memory sessions cannot be recovered after their process exits. Existing private CSV files are discovered and their metadata persisted when listed. Back up old quota records before rollout; migrate them explicitly if preserving today's allowance matters. Previously shared knowledge uploads need an explicit owner before being moved into a user's knowledge directory.

Uploads default to 5 MiB of UTF-8 content (`MAX_UPLOAD_BYTES`); the request body has a separate bounded JSON envelope. Filenames must be plain basenames and resolved paths must stay within storage roots. All successful LLM calls�including routing, suggestions, and widgets�count toward the UTC daily quota. Each call checks remaining allowance; the last in-flight call can exceed the remaining budget because usage is reported after generation.

Run deterministic checks with `pip install -r requirements-dev.txt` and `python -m pytest`. Tests use isolated SQLite by default and no live LLM credentials. Set `TEST_DATABASE_URL` to a **disposable** PostgreSQL database to test its actual locking and persistence; the test fixture clears its application records. GitHub Actions runs the suite against PostgreSQL 16 and builds the frontend. Live Supabase OAuth and provider availability require separate deployment smoke testing.

---

## Operational notes

Structured request logs contain request IDs, method, status, and duration, without authorization headers or request bodies. Validation failures and production errors return generic messages.

Provider pricing and quotas depend on your accounts. Configure spending limits directly with each provider.
