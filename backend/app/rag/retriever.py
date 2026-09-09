"""RAG Vector Store Retriever: performs similarity search over indexed chunks."""
from typing import Any, Dict, List, Optional
import numpy as np

from backend.app.rag.indexer import DocumentIndexer, DocumentChunk


class DocumentRetriever:
    """Retrieves relevant documentation passages given a natural language query."""

    def __init__(self, indexer: Optional[DocumentIndexer] = None):
        self.indexer = indexer or DocumentIndexer()
        self._matrix: Optional[np.ndarray] = None
        self._chunks: List[DocumentChunk] = []
        self.refresh()

    def refresh(self):
        """Re-index documents from disk and build vector matrix."""
        self._chunks = self.indexer.build_index()
        if self._chunks and self._chunks[0].vector is not None:
            # Stack chunk vectors into matrix (N_chunks x Vocab_size)
            vectors = [c.vector for c in self._chunks if c.vector is not None]
            self._matrix = np.vstack(vectors)
        else:
            self._matrix = None

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve top_k matching chunks for query ranked by cosine similarity."""
        if not self._chunks or self._matrix is None:
            return []

        q_vec = self.indexer.vectorize_query(query)
        if len(q_vec) == 0 or np.linalg.norm(q_vec) == 0:
            return []

        # Cosine similarity is dot product of normalized vectors
        scores = np.dot(self._matrix, q_vec)

        # Rank indices descending
        ranked_indices = np.argsort(scores)[::-1]

        results = []
        for idx in ranked_indices[:top_k]:
            score = float(scores[idx])
            if score <= 0.001:
                continue  # Skip irrelevant passages

            chunk = self._chunks[idx]
            results.append({
                "source": chunk.source,
                "title": chunk.title,
                "content": chunk.content,
                "score": round(score, 4),
            })

        return results


# Global singleton retriever instance
default_retriever = DocumentRetriever()

def get_user_retriever(user_id):
    from backend.app.config import KNOWLEDGE_DIR
    from backend.app.paths import inside
    return DocumentRetriever(DocumentIndexer(inside(KNOWLEDGE_DIR, user_id)))
