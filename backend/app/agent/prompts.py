"""System prompts and instruction templates for the Agent / Router and Coordinator."""
from typing import Any, Dict, List, Optional


ROUTER_SYSTEM_PROMPT = """You are an intelligent query router in the Visiq autonomous data analysis platform.
Analyze the user query and conversational history to determine the necessary analysis route:
- 'structured': Query asks for calculations, aggregations, counts, filtering on dataset records.
- 'rag': Query asks for definitions, methodology, column meaning, or dataset documentation.
- 'hybrid': Query requires both (e.g. data calculation along with definition verification).
"""

COORDINATOR_SYSTEM_PROMPT = """You are Visiq, an expert autonomous data analyst agent.
You have access to structured data tools and RAG search tools.
Answer user questions accurately using deterministic tool calls rather than guessing.
"""


def build_router_prompt(
    query: str,
    context: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Prompt to classify query intent into 'structured', 'rag', or 'hybrid'."""
    context_str = ""
    if context:
        recent = context[-3:]
        lines = [
            f"{m.get('role', 'user').capitalize()}: {m.get('content', '')}"
            for m in recent
            if m.get("content")
        ]
        if lines:
            context_str = "CONVERSATION CONTEXT:\n" + "\n".join(lines) + "\n\n"

    return f"""{ROUTER_SYSTEM_PROMPT}

CLASSIFICATION RULES:
1. 'structured':
   - Query asks for calculations, aggregations, counts, filters, sorting, column values, or statistical summaries of dataset rows.
   - Examples: "Top 5 oldest movies", "How many movies are there?", "Average salary by experience level", "What columns are in this data?".

2. 'rag':
   - Query asks for definitions, terminology, rating criteria, abbreviations, methodology, or documentation context without requiring dataset calculations.
   - Examples: "What does TV-MA mean?", "What is the criteria for a PG-13 rating?", "Explain the difference between full-time and part-time in the notes".

3. 'hybrid':
   - Query explicitly requires BOTH empirical dataset numbers/filtering AND domain documentation/definitions/explanations.
   - Examples: "List all TV-MA shows and explain why they received this rating", "Count titles in each genre and explain the rating guidelines for each".

{context_str}USER QUERY:
"{query}"

RESPONSE FORMAT:
Return ONLY a valid JSON object with NO markdown fences, backticks, or extra text:
{{
  "route": "structured" | "rag" | "hybrid",
  "reason": "brief 1-sentence reason for this classification"
}}
"""



def build_tool_selection_prompt(
    question: str,
    data_description: str,
    tools_schemas: List[Dict[str, Any]],
    history: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Construct prompt for the LLM to choose the appropriate tool and arguments."""
    tools_formatted = []
    for s in tools_schemas:
        name = s.get("name", "")
        if name in ("generate_chart",):
            continue  # Charting is handled post-execution by the coordinator

        params = s.get("parameters", {}).get("properties", {})
        required = s.get("parameters", {}).get("required", [])
        params_str = ", ".join(
            f"{p}: {v.get('type')}" + (" (required)" if p in required else "")
            for p, v in params.items()
        )
        desc = s.get("description", "").strip().replace("\n", " ")
        tools_formatted.append(f"- {name}({params_str}): {desc}")

    tools_text = "\n".join(tools_formatted)

    history_text = ""
    if history:
        recent = history[-4:]
        history_lines = [
            f"{m.get('role', 'user').capitalize()}: {m.get('content', '')}"
            for m in recent
            if m.get("content")
        ]
        if history_lines:
            history_text = "RECENT CONVERSATION HISTORY:\n" + "\n".join(history_lines) + "\n\n"

    return f"""You are a senior data analyst agent. You will be given a description of a dataset, conversational history, and a user's question.
Your job is to select the single best tool to answer the question, and provide its exact arguments.

DATASET SCHEMA & DESCRIPTION:
{data_description}

AVAILABLE TOOLS:
{tools_text}
- unsupported(reason: string): Call this ONLY if the question genuinely cannot be answered using the available columns or data.

TOOL SELECTION RULES:
1. Always use exact column names from the dataset schema.
2. For questions asking for "most common", "top categories", or frequencies of a single column (e.g. 'most common genres', 'top countries', 'distribution of rating'), use 'get_unique_values' or 'group_data'.
3. For questions asking for single summary statistics (e.g. 'how many movies', 'average salary', 'total count'), use 'aggregate_data' or 'filter_rows'.
4. For questions asking to find or list records matching specific criteria (e.g. 'movies directed by Spielberg', 'titles from 2020'), use 'filter_rows'.
5. For questions sorting the raw dataset records (e.g. '5 oldest movies', 'highest paying jobs'), use 'sort_data'.
6. For questions requiring grouping by one column and aggregating another (e.g. 'average salary by job title'), use 'group_data'.
7. If the user asks about dataset structure, row count, or available columns, use 'get_dataset_schema'.
8. If the user asks about definitions or methodology documentation, use 'search_documents'.
9. When the user asks for a chart, graph, line graph, or trend over time (e.g. 'create me a line graph with it', 'plot average seasons', 'chart by year'):
   - Use 'group_data' grouping by a time/ordered column (like 'release_year' or 'date_added') or categorical column so that multiple data points can be plotted!
   - Example: 'what are the average number of season per tv show create me a line graph with it' -> tool: 'group_data', parameters: {{"by_column": "release_year", "agg_column": "duration_seasons", "agg_func": "mean"}}.

10. SPECIFIC ENTITY / CRITERIA SEARCH (e.g. 'How many titles are there from Wakanda?', 'Movies directed by Tarantino'):
    - ALWAYS use 'filter_rows' with the relevant column (e.g. column='country', operator='contains', value='Wakanda').
    - NEVER use 'get_unique_values' when checking for a specific named entity, country, person, or title.

11. AMBIGUOUS, SUBJECTIVE, OR MISSING METRICS (e.g. 'best', 'worst', 'most popular', 'top rated', 'most successful'):
    - First check the dataset schema to see if an empirical quality score, review rating, views, or popularity column exists.
    - IMPORTANT NOTE: In catalog datasets like Netflix, the 'rating' column is a content maturity advisory (e.g. TV-MA, PG-13), NOT a quality or review score!
    - If the user asks for a subjective quality ('best titles', 'worst movies', 'most popular') and the dataset DOES NOT have an empirical rating/score/popularity column:
      * Choose 'unsupported' explaining clearly that the dataset does not contain quality scores, review ratings, or popularity metrics (clarifying that 'rating' is only content maturity), and suggest alternatives (e.g. by release year, runtime, or genre).
      * Do NOT silently assume an arbitrary proxy (like runtime) as 'best' without user confirmation.

{history_text}USER QUESTION:
"{question}"

RESPONSE FORMAT:
Return ONLY a valid JSON object with no markdown fences, backticks, or extra explanation:
{{
  "thought": "brief 1-sentence reasoning for selecting this tool and arguments",
  "tool": "<tool_name>",
  "parameters": {{ ... }}
}}
"""


def build_summary_prompt(
    question: str,
    tool_name: str,
    result: Any,
    assumption: Optional[str] = None,
) -> str:
    """Prompt to generate a concise plain-English explanation of analysis results."""
    assumption_instruction = ""
    if assumption:
        assumption_instruction = f"""
IMPORTANT DISCLOSURE ON ASSUMPTIONS:
An analytical proxy or assumption was used: "{assumption}"
You MUST explicitly state this caveat upfront in your summary (e.g., clarify that the dataset does not measure quality/reviews/popularity, and explain what proxy metric was examined instead).
"""

    return f"""You are a professional data analyst.
The user asked: "{question}"

The analysis executed the '{tool_name}' tool and produced this result:
{result}
{assumption_instruction}
Write a concise, professional 2-3 sentence plain-English summary explaining what the result shows.
Mention specific numbers, categories, or metrics where relevant.
If the result has 0 records or matches (e.g. searching for an entity that is not in the data), clearly state that no records were found.
If an assumption was made, disclose it transparently.
Do not mention that an AI or tool was used. Maintain an objective, informative tone.
"""


def build_rag_summary_prompt(question: str, excerpts: List[Dict[str, Any]]) -> str:
    """Prompt to synthesize an answer from unstructured document search excerpts."""
    excerpts_str = "\n\n".join(
        f"Source: {e.get('source', 'Unknown')}\nExcerpt: {e.get('content', '')}"
        for e in excerpts
    )
    return f"""You are a knowledge assistant for dataset documentation.
The user asked: "{question}"

The following documentation excerpts were retrieved:
{excerpts_str}

Write a clear, direct, and helpful answer answering the user's question based on the documentation.
If the information is not present in the excerpts, state that fact clearly.
"""


def build_hybrid_summary_prompt(
    question: str,
    tool_result: Any,
    excerpts: List[Dict[str, Any]],
) -> str:
    """Prompt to synthesize empirical data calculation with documentation excerpts."""
    excerpts_str = "\n\n".join(
        f"Source: {e.get('source', 'Unknown')}\nExcerpt: {e.get('content', '')}"
        for e in excerpts
    )
    return f"""You are a senior data analyst synthesizing both empirical data analysis and dataset documentation.
The user asked: "{question}"

Empirical Data Analysis Result:
{tool_result}

Documentation & Knowledge Context:
{excerpts_str}

Write a comprehensive, professional 2-4 sentence summary that presents the empirical numbers from the data and contextualizes them using the documentation.
Mention specific figures and key definitions where relevant.
"""
