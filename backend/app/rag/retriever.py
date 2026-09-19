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


def get_user_retriever(user_id):
    from backend.app.config import KNOWLEDGE_DIR
    from backend.app.paths import inside
    class UserIndexer(DocumentIndexer):
        def load_documents(self):
            documents = {d['filename']: d for d in super().load_documents()}
            try:
                from backend.app.file_storage import file_store
                for doc_path in file_store.list_files(user_id, kind="doc"):
                    if doc_path.name not in documents:
                        content = file_store.load(user_id, doc_path.name, kind="doc")
                        if content:
                            documents[doc_path.name] = {'filename': doc_path.name, 'content': content}
            except Exception:
                pass
            # Only these bundled public reference documents are shared. Legacy
            # uploads in the global directory are never implicitly made public.
            for name in ('methodology_notes.md', 'netflix_data_dictionary.md'):
                path = inside(KNOWLEDGE_DIR, name)
                if name not in documents and path.is_file():
                    documents[name] = {'filename': name, 'content': path.read_text(encoding='utf-8')}
            return list(documents.values())
    return DocumentRetriever(UserIndexer(inside(KNOWLEDGE_DIR, user_id)))
