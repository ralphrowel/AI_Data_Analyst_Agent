"""RAG Document Indexer: parses, chunks, and vectorizes dataset documentation."""
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from backend.app.config import KNOWLEDGE_DIR


class DocumentChunk:
    """A single chunked passage from a knowledge document."""

    def __init__(
        self,
        chunk_id: str,
        source: str,
        title: str,
        content: str,
        vector: Optional[np.ndarray] = None,
    ):
        self.chunk_id = chunk_id
        self.source = source
        self.title = title
        self.content = content
        self.vector = vector

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "source": self.source,
            "title": self.title,
            "content": self.content,
        }


def _tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into clean words."""
    cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
    tokens = [w.strip() for w in re.split(r"[\s_]+", cleaned) if len(w.strip()) > 1]
    return tokens


class DocumentIndexer:
    """Loads unstructured markdown/text documents, chunks them, and builds vector representations."""

    def __init__(self, knowledge_dir: Path = KNOWLEDGE_DIR):
        self.knowledge_dir = knowledge_dir
        self.vocabulary: Dict[str, int] = {}
        self.idf: np.ndarray = np.array([])
        self.chunks: List[DocumentChunk] = []

    def load_documents(self) -> List[Dict[str, str]]:
        """Scan knowledge directory and read all markdown and text files."""
        docs = []
        if not self.knowledge_dir.exists():
            return docs

        for ext in ("*.md", "*.txt"):
            for file_path in self.knowledge_dir.glob(ext):
                try:
                    from backend.app.paths import inside
                    file_path = inside(self.knowledge_dir, file_path.name)
                    with open(file_path, "r", encoding="utf-8") as f:
                        docs.append({
                            "filename": file_path.name,
                            "content": f.read(),
                        })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        return docs

    def chunk_document(self, filename: str, text: str) -> List[DocumentChunk]:
        """Split document by markdown headings or paragraphs into coherent passages (~200-300 words)."""
        raw_sections = re.split(r"\n(?=#{1,3}\s)", text)
        chunks: List[DocumentChunk] = []
        chunk_counter = 0

        for section in raw_sections:
            trimmed = section.strip()
            if not trimmed:
                continue

            # Extract title if section starts with markdown header
            lines = trimmed.splitlines()
            title = filename
            if lines[0].startswith("#"):
                title = lines[0].lstrip("#").strip()

            # If section is small/medium (under ~2000 chars), keep as single chunk
            if len(trimmed) <= 2000:
                chunk_id = f"{filename}_chunk_{chunk_counter}"
                chunks.append(DocumentChunk(chunk_id=chunk_id, source=filename, title=title, content=trimmed))
                chunk_counter += 1
            else:
                # Split large sections by paragraphs
                paragraphs = [p.strip() for p in trimmed.split("\n\n") if p.strip()]
                current_block = []
                current_len = 0

                for p in paragraphs:
                    current_block.append(p)
                    current_len += len(p)
                    if current_len >= 1200:
                        content = "\n\n".join(current_block)
                        chunk_id = f"{filename}_chunk_{chunk_counter}"
                        chunks.append(DocumentChunk(chunk_id=chunk_id, source=filename, title=title, content=content))
                        chunk_counter += 1
                        current_block = []
                        current_len = 0

                if current_block:
                    content = "\n\n".join(current_block)
                    chunk_id = f"{filename}_chunk_{chunk_counter}"
                    chunks.append(DocumentChunk(chunk_id=chunk_id, source=filename, title=title, content=content))
                    chunk_counter += 1

        return chunks

    def build_index(self) -> List[DocumentChunk]:
        """Ingest all knowledge documents, chunk them, and compute normalized TF-IDF vector embeddings."""
        docs = self.load_documents()
        all_chunks: List[DocumentChunk] = []
        for doc in docs:
            chunks = self.chunk_document(doc["filename"], doc["content"])
            all_chunks.extend(chunks)

        if not all_chunks:
            self.chunks = []
            return []

        # 1. Build vocabulary and document frequencies
        vocab: Dict[str, int] = {}
        doc_counts: Dict[str, int] = {}
        tokenized_chunks = []

        for chunk in all_chunks:
            # Include both title and content for high retrieval accuracy
            full_text = f"{chunk.title} {chunk.content}"
            tokens = _tokenize(full_text)
            tokenized_chunks.append(tokens)

            unique_tokens = set(tokens)
            for t in unique_tokens:
                doc_counts[t] = doc_counts.get(t, 0) + 1
                if t not in vocab:
                    vocab[t] = len(vocab)

        vocab_size = len(vocab)
        num_docs = len(all_chunks)

        # 2. Compute IDF vector
        idf = np.zeros(vocab_size, dtype=np.float32)
        for term, idx in vocab.items():
            df = doc_counts.get(term, 1)
            idf[idx] = math.log((num_docs + 1.0) / (df + 1.0)) + 1.0

        # 3. Compute L2-normalized TF-IDF vector for each chunk
        for i, chunk in enumerate(all_chunks):
            tokens = tokenized_chunks[i]
            tf = np.zeros(vocab_size, dtype=np.float32)
            for t in tokens:
                idx = vocab.get(t)
                if idx is not None:
                    tf[idx] += 1.0

            # Sublinear term frequency scaling: 1 + log(tf)
            non_zeros = tf > 0
            tf[non_zeros] = 1.0 + np.log(tf[non_zeros])
            tfidf = tf * idf

            norm = np.linalg.norm(tfidf)
            if norm > 0:
                chunk.vector = tfidf / norm
            else:
                chunk.vector = tfidf

        self.vocabulary = vocab
        self.idf = idf
        self.chunks = all_chunks
        return all_chunks

    def vectorize_query(self, query: str) -> np.ndarray:
        """Project a query into the indexed vector space with L2 normalization."""
        if not self.vocabulary or len(self.idf) == 0:
            return np.array([])

        vocab_size = len(self.vocabulary)
        tokens = _tokenize(query)
        tf = np.zeros(vocab_size, dtype=np.float32)

        for t in tokens:
            idx = self.vocabulary.get(t)
            if idx is not None:
                tf[idx] += 1.0

        non_zeros = tf > 0
        tf[non_zeros] = 1.0 + np.log(tf[non_zeros])
        tfidf = tf * self.idf

        norm = np.linalg.norm(tfidf)
        if norm > 0:
            return tfidf / norm
        return tfidf
