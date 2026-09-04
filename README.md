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
| LLM (primary) | Google Gemini free tier (`gemini-2.5-flash`) |
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
- **LLM fallback** — Gemini's free tier caps at 20 requests/day. When exhausted, calls transparently retry against Groq, with the UI showing which model actually answered.
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

Set `GEMINI_API_KEY`, `GROQ_API_KEY`, and `ALLOWED_ORIGINS` in `.env` before starting the backend.

---

## Notes

- Never enable billing on the Gemini free-tier Google Cloud project — the entire stack is designed to run for free.
- Groq's free tier (~1,000 requests/day) comfortably absorbs overflow once Gemini's 20/day quota is reached.