"""Tool registry setup — registers all structured tools with Gemini-compatible schemas.

Importing this module populates `default_registry` so the AgentCoordinator
can discover available tools and pass their schemas to Gemini for tool calling.

IMPORTANT: DataFrame (`df`) parameters are NOT exposed in the schemas.
Gemini only decides *which* tool to call and *what arguments* to pass;
the coordinator injects the active DataFrame at execution time.
"""

from backend.app.tools.base import default_registry
from backend.app.tools.structured_tools import (
    get_dataset_schema,
    filter_rows,
    aggregate_data,
    group_data,
    sort_data,
    get_unique_values,
)
from backend.app.tools.chart_tool import generate_chart
from backend.app.tools.rag_tools import search_documents


# ---------------------------------------------------------------------------
# Gemini function declaration schemas
#
# Format follows the google.genai function calling specification:
#   name        — tool name (must match registry key)
#   description — what the tool does (Gemini uses this to decide when to call)
#   parameters  — JSON Schema-style object describing expected arguments
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = {
    "get_dataset_schema": {
        "name": "get_dataset_schema",
        "description": (
            "Return the dataset's column names, data types, missing-value counts, "
            "and total row count. Call this when the user asks about the structure "
            "of the data, what columns exist, or how many rows the dataset has."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "filter_rows": {
        "name": "filter_rows",
        "description": (
            "Filter dataset rows by a column value. Returns matching rows. "
            "Use this when the user asks to find, search, or list items matching "
            "specific criteria (e.g., 'show me horror movies', 'find titles by director X')."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "column": {
                    "type": "string",
                    "description": "The column to filter on (e.g., 'type', 'country', 'listed_in').",
                },
                "operator": {
                    "type": "string",
                    "description": "The comparison operator to use.",
                    "enum": ["eq", "contains"],
                },
                "value": {
                    "type": "string",
                    "description": "The value to filter for.",
                },
            },
            "required": ["column", "operator", "value"],
        },
    },
    "aggregate_data": {
        "name": "aggregate_data",
        "description": (
            "Compute a single aggregate metric (count, mean, sum, min, max) on a column. "
            "Use this for questions like 'how many movies?', 'average duration?', "
            "'total count of TV shows?'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "column": {
                    "type": "string",
                    "description": "The column to aggregate.",
                },
                "agg_func": {
                    "type": "string",
                    "description": "The aggregation function to apply.",
                    "enum": ["count", "mean", "sum", "min", "max"],
                },
            },
            "required": ["column", "agg_func"],
        },
    },
    "group_data": {
        "name": "group_data",
        "description": (
            "Group the dataset by one column and aggregate another column. "
            "Use this for questions like 'count of titles by country', "
            "'average duration by rating', 'top 10 directors by number of titles'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "by_column": {
                    "type": "string",
                    "description": "The column to group by (e.g., 'country', 'rating', 'type').",
                },
                "agg_column": {
                    "type": "string",
                    "description": "The column to aggregate within each group.",
                },
                "agg_func": {
                    "type": "string",
                    "description": "The aggregation function.",
                    "enum": ["count", "mean", "sum", "min", "max"],
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of groups to return (default 10).",
                },
            },
            "required": ["by_column", "agg_column", "agg_func"],
        },
    },
    "sort_data": {
        "name": "sort_data",
        "description": (
            "Sort the dataset by a column and return the top rows. "
            "Use this for 'top N' or 'bottom N' questions that need raw row data, "
            "like 'newest 5 titles', 'longest movies'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "by_column": {
                    "type": "string",
                    "description": "The column to sort by.",
                },
                "ascending": {
                    "type": "boolean",
                    "description": "Sort ascending (true) or descending (false). Default is false.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of rows to return (default 10).",
                },
            },
            "required": ["by_column"],
        },
    },
    "get_unique_values": {
        "name": "get_unique_values",
        "description": (
            "Return the top unique values and their frequencies for a column. "
            "Use this for 'most common', 'most frequent', or 'what are the categories' "
            "questions (e.g., 'most common genres', 'top countries')."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "column": {
                    "type": "string",
                    "description": "The column to get unique values from.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of unique values to return (default 20).",
                },
            },
            "required": ["column"],
        },
    },
    "generate_chart": {
        "name": "generate_chart",
        "description": (
            "Generate a chart (bar, line, or pie) from a previous tool's result. "
            "Call this AFTER another tool has returned data that should be visualized."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "description": "The chart type to generate. 'auto' selects automatically.",
                    "enum": ["bar", "line", "pie", "auto"],
                },
            },
            "required": [],
        },
    },
    "search_documents": {
        "name": "search_documents",
        "description": (
            "Search unstructured documentation, data dictionaries, and notes for definitions, "
            "domain context, column meanings, or methodology."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of relevant passages to retrieve (default 3).",
                },
            },
            "required": ["query"],
        },
    },
}


# ---------------------------------------------------------------------------
# Tool function mapping
#
# Maps tool names to their implementation functions.
# The coordinator resolves `df` at call time — these are the raw functions.
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "get_dataset_schema": get_dataset_schema,
    "filter_rows": filter_rows,
    "aggregate_data": aggregate_data,
    "group_data": group_data,
    "sort_data": sort_data,
    "get_unique_values": get_unique_values,
    "generate_chart": generate_chart,
    "search_documents": search_documents,
}



# ---------------------------------------------------------------------------
# Register everything into the global default registry
# ---------------------------------------------------------------------------

def setup_registry(registry=None):
    """Register all tools and schemas into the given registry (or the global default)."""
    reg = registry or default_registry
    for name, func in TOOL_FUNCTIONS.items():
        reg.register(name=name, func=func, schema=TOOL_SCHEMAS.get(name))
    return reg


# Auto-register on import so the registry is ready when the app starts
setup_registry()
