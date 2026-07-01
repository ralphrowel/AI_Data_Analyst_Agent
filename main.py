import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai

from dataloader import load_data, describe_dataframe
from query_planner import get_query_plan, get_summary
from query_executor import execute_plan
from chart_generator import generate_chart

load_dotenv(dotenv_path=Path(__file__).parent / ".env")
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter your question: ")

df = load_data("data/netflix_titles.csv")
description = describe_dataframe(df)

print(f"\nQuestion: {question}")
print("---")

plan = get_query_plan(question, description, client)
print(f"Plan: {plan}")

result = execute_plan(df, plan)
print(f"Result: {result}")

summary = get_summary(question, result, client)
print(f"\nSummary:\n{summary}")

chart_path = "chart.png"
generate_chart(result, chart_path)
print(f"\nChart saved: {chart_path}")
