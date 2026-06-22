import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

from dataloader import load_data, describe_dataframe
from query_planner import get_query_plan

# Setup
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Stage 2: load and describe the data
df = load_data("data/netflix_titles.csv")
description = describe_dataframe(df)

# Stage 3: ask Gemini to turn a question into a structured plan
question = "What is the average duration of TV shows in minutes?"
plan = get_query_plan(question, description, client)

print("Question:", question)
print("Plan returned by Gemini:")
print(plan)