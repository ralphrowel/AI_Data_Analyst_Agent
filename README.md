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
├── .env                  # GEMINI_API_KEY, GROQ_API_KEY, ALLOWED_ORIGINS — never committed
├── api.py                # FastAPI entry point — POST /api/ask, GET /api/suggestions
├── dataloader.py          # load_data(), describe_dataframe(), COLUMN_NOTES
├── query_planner.py       # get_query_plan(), get_summary(), Gemini/Groq fallback logic
├── query_executor.py      # Executes JSON plans safely against the DataFrame
├── chart_generator.py     # Matplotlib chart generation + Auto chart-type heuristic
├── data/
│   └── netflix_titles.csv
└── frontend/
    ├── src/
    │   ├── api.js             # Fetch calls to FastAPI
    │   └── components/
    │       ├── App.jsx            # Root state, dark mode, active model tracking
    │       ├── Header.jsx         # Model badge, dark mode + chart theme toggles
    │       ├── ChatPanel.jsx / ChartPanel.jsx
    │       ├── MessageBubble.jsx / SystemMessage.jsx
    │       └── TokenUsageDisplay.jsx
```

---

## Status

**Stages 1–9 complete** — full pipeline, chart rendering, real token usage tracking, dark mode, LLM fallback, and all known pre-deployment blockers resolved (CORS narrowed, chart generation moved off disk).

**Next: Stage 10** — deploy React to Vercel, FastAPI to Render or Railway.

---

## Running locally

```bash
# Backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn api:app --reload

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