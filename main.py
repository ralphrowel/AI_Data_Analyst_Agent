import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai

from dataloader import load_data, describe_dataframe
from data_profiler import profile_dataframe
from query_planner import get_query_plan, get_summary
from query_executor import execute_plan
from chart_generator import generate_chart

load_dotenv(dotenv_path=Path(__file__).parent / ".env")
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

if len(sys.argv) < 2:
    print("Usage: python main.py <csv_path> [question]")
    sys.exit(1)

potential = sys.argv[1]
if potential.endswith(".csv") or Path(potential).exists():
    csv_path = potential
    question = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else input("Enter your question: ")
else:
    csv_dir = Path(__file__).parent / "data"
    csv_files = sorted(csv_dir.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in data/")
        sys.exit(1)
    csv_path = str(csv_files[0])
    question = " ".join(sys.argv[1:])

df = load_data(csv_path)
description = describe_dataframe(df)
profile = profile_dataframe(df)
full_context = description + "\n\n" + profile

print(f"Dataset: {csv_path}")
print(f"Question: {question}")
print("---")

plan = get_query_plan(question, full_context, client)
print(f"Plan: {plan}")

result = execute_plan(df, plan)
print(f"Result: {result}")

summary = get_summary(question, result, client)
print(f"\nSummary:\n{summary}")

chart_path = "chart.png"
generate_chart(result, chart_path)
print(f"\nChart saved: {chart_path}")
