from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # TODO: initialize chromadb client + collection
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # Embed content
        embedding = self._embedding_fn(doc.content)
        return {
            'id': doc.id,
            'content': doc.content,
            'embedding': embedding,
            'metadata': dict(doc.metadata) if doc.metadata else {},
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_emb = self._embedding_fn(query)
        scored = []
        for rec in records:
            sim = _dot(query_emb, rec['embedding'])
            rec_copy = dict(rec)
            rec_copy['score'] = sim
            scored.append(rec_copy)
        scored.sort(key=lambda r: r['score'], reverse=True)
        # Only return keys required by test: id, content, score, metadata
        return [
            {k: rec[k] for k in rec if k in ('id', 'content', 'score', 'metadata')}
            for rec in scored[:top_k]
        ]

    def add_documents(self, docs: list[Document]) -> None:
        if self._use_chroma and self._collection is not None:
            ids = [doc.id for doc in docs]
            contents = [doc.content for doc in docs]
            embeddings = [self._embedding_fn(doc.content) for doc in docs]
            metadatas = [dict(doc.metadata) if doc.metadata else {} for doc in docs]
            self._collection.add(ids=ids, documents=contents, embeddings=embeddings, metadatas=metadatas)
        else:
            for doc in docs:
                rec = self._make_record(doc)
                self._store.append(rec)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self._use_chroma and self._collection is not None:
            results = self._collection.query(query_texts=[query], n_results=top_k)
            # ChromaDB returns dict with ids, documents, metadatas, distances
            out = []
            for i in range(len(results['ids'][0])):
                out.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': 1 - results['distances'][0][i]  # Chroma returns distance, convert to similarity
                })
            return out
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        else:
            return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        if self._use_chroma and self._collection is not None and metadata_filter:
            # ChromaDB supports where filter
            results = self._collection.query(query_texts=[query], n_results=top_k, where=metadata_filter)
            out = []
            for i in range(len(results['ids'][0])):
                out.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': 1 - results['distances'][0][i]
                })
            return out
        else:
            # In-memory: filter first, then search
            filtered = self._store
            if metadata_filter:
                def match(meta, filt):
                    return all(meta.get(k) == v for k, v in filt.items())
                filtered = [rec for rec in self._store if match(rec['metadata'], metadata_filter)]
            return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        removed = False
        if self._use_chroma and self._collection is not None:
            # ChromaDB: delete by id
            self._collection.delete(ids=[doc_id])
            removed = True  # Assume success
        else:
            before = len(self._store)
            self._store = [rec for rec in self._store if rec['id'] != doc_id]
            removed = len(self._store) < before
        return removed
