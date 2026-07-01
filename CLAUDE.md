# Ai Data Analyst Agent

## Project Overview

Python-based AI data analyst agent using Google Gemini. Loads CSV data, describes its structure, and translates natural language questions into structured query plans executed on the data.

## Stack

- Python 3.x with `google-genai` SDK (Gemini 2.5 Flash)
- pandas for data loading and description
- `.env` for `GEMINI_API_KEY`

## Project Structure

- `main.py` — entry point; wires data loading, description, and query planning
- `dataloader.py` — CSV loading and DataFrame description with column notes
- `query_planner.py` — prompt construction and Gemini API call for structured query plans
- `data/netflix_titles.csv` — sample dataset

## BMAD Method

This project uses the BMAD Method for structured AI-driven development.

- Skills are in `.claude/skills/` — invoke with `/skills/<skill-name>`
- Config is in `_bmad/` — module configs under `_bmad/core/config.yaml` and `_bmad/bmm/config.yaml`
- Planning artifacts go to `_bmad-output/planning-artifacts/`
- Implementation artifacts go to `_bmad-output/implementation-artifacts/`
- Project knowledge lives in `docs/`

### Getting Started with BMAD

Invoke the help skill to orient yourself:

```
/skills/bmad-help
```

### Key Agents

| Skill | Agent | Role |
|-------|-------|------|
| `bmad-agent-analyst` | Mary | Business Analyst |
| `bmad-agent-pm` | John | Product Manager |
| `bmad-agent-architect` | Winston | System Architect |
| `bmad-agent-dev` | Amelia | Senior Developer |
| `bmad-agent-ux-designer` | Sally | UX Designer |
| `bmad-agent-tech-writer` | Paige | Technical Writer |
