"""RAG Document Indexer: parses and chunks dataset documentation."""
from pathlib import Path
from typing import List, Dict
from backend.app.config import KNOWLEDGE_DIR


class DocumentIndexer:
    """Loads unstructured documentation from data/knowledge and prepares chunks."""

    def __init__(self, knowledge_dir: Path = KNOWLEDGE_DIR):
        self.knowledge_dir = knowledge_dir

    def load_documents(self) -> List[Dict[str, str]]:
        docs = []
        if not self.knowledge_dir.exists():
            return docs

        for file_path in self.knowledge_dir.glob("*.md"):
            with open(file_path, "r", encoding="utf-8") as f:
                docs.append({
                    "filename": file_path.name,
                    "content": f.read(),
                })
        return docs
