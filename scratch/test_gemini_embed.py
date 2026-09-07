import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app.llm.client import get_gemini_client

client = get_gemini_client()
if client:
    for m in client.models.list():
        if "embed" in m.name.lower():
            print("Found embedding model:", m.name)
