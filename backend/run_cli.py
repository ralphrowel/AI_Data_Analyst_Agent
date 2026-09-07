import sys
from pathlib import Path

# Add project root to sys.path if run directly
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.config import DEFAULT_DATASET_PATH
from backend.app.llm.client import get_gemini_client
from backend.app.data_engine.loader import load_data, describe_dataframe
from backend.app.data_engine.profiler import profile_dataframe
from backend.app.legacy.query_planner import get_query_plan, get_summary
from backend.app.legacy.query_executor import execute_plan
from backend.app.tools.chart_tool import generate_chart

client = get_gemini_client()

if len(sys.argv) < 2:
    print("Usage: python backend/run_cli.py <csv_path> [question]")
    print(f"Defaulting to: {DEFAULT_DATASET_PATH}")
    csv_path = str(DEFAULT_DATASET_PATH)
    question = input("Enter your question: ")
else:
    potential = sys.argv[1]
    if potential.endswith(".csv") or Path(potential).exists():
        csv_path = potential
        question = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else input("Enter your question: ")
    else:
        csv_path = str(DEFAULT_DATASET_PATH)
        question = " ".join(sys.argv[1:])

df = load_data(csv_path)
description = describe_dataframe(df)
profile = profile_dataframe(df)
full_context = description + "\n\n" + profile

print(f"Dataset: {csv_path}")
print(f"Question: {question}")
print("---")

plan_res = get_query_plan(question, full_context, client)
plan = plan_res["plan"]
print(f"Plan: {plan}")

result = execute_plan(df, plan)
print(f"Result: {result}")

summary_res = get_summary(question, result, client)
print(f"\nSummary:\n{summary_res['summary']}")

chart_res = generate_chart(result)
chart_b64 = chart_res[0] if isinstance(chart_res, tuple) else chart_res
print(f"\nChart generated: {'Yes (base64)' if chart_b64 else 'None'}")
