from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.chunking import RecursiveChunker
from src.models import Document
from src.store import EmbeddingStore

SAMPLE_FILES = [
    "data\data.md",

]


def load_documents_from_files(file_paths: list[str]) -> list[Document]:
    """Load documents from file paths for the manual demo."""
    allowed_extensions = {".md", ".txt"}
    documents: list[Document] = []

    for raw_path in file_paths:
        path = Path(raw_path)

        if path.suffix.lower() not in allowed_extensions:
            print(f"Skipping unsupported file type: {path} (allowed: .md, .txt)")
            continue

        if not path.exists() or not path.is_file():
            print(f"Skipping missing file: {path}")
            continue

        content = path.read_text(encoding="utf-8")
        documents.append(
            Document(
                id=path.stem,
                content=content,
                metadata={"source": str(path), "extension": path.suffix.lower()},
            )
        )

    return documents


def chunk_documents(documents: list[Document], chunk_size: int = 1500) -> list[Document]:
    """Split large documents into smaller chunks for safer embedding."""
    chunker = RecursiveChunker(chunk_size=chunk_size)
    chunked_docs: list[Document] = []
    for doc in documents:
        chunks = chunker.chunk(doc.content)
        if len(chunks) <= 1:
            chunked_docs.append(doc)
            continue
        for index, chunk in enumerate(chunks):
            chunked_docs.append(
                Document(
                    id=f"{doc.id}#chunk{index}",
                    content=chunk,
                    metadata={
                        **doc.metadata,
                        "parent_id": doc.id,
                        "chunk_index": index,
                    },
                )
            )
    return chunked_docs


def demo_llm(prompt: str) -> str:
    """A simple mock LLM for manual RAG testing."""
    preview = prompt[:100].replace("\n", " ")
    return f"[DEMO LLM] Generated answer from prompt preview: {preview}..."


def build_openai_llm() -> callable:
    """Create an OpenAI-backed LLM callable. Falls back to demo_llm on errors."""
    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    def _llm(prompt: str) -> str:
        try:
            from openai import OpenAI

            client = OpenAI()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            message = response.choices[0].message.content
            return message.strip() if message else ""
        except Exception as exc:
            return f"[DEMO LLM] OpenAI call failed: {exc}"

    return _llm


def run_manual_demo(question: str | None = None, sample_files: list[str] | None = None) -> int:
    files = sample_files or SAMPLE_FILES
    query = question or "Summarize the key information from the loaded files."

    print("=== Manual File Test ===")
    print("Accepted file types: .md, .txt")
    print("Input file list:")
    for file_path in files:
        print(f"  - {file_path}")

    docs = load_documents_from_files(files)
    if not docs:
        print("\nNo valid input files were loaded.")
        print("Create files matching the sample paths above, then rerun:")
        print("  python3 main.py")
        return 1

    print(f"\nLoaded {len(docs)} documents")
    for doc in docs:
        print(f"  - {doc.id}: {doc.metadata['source']}")

    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            embedder = LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception:
            embedder = _mock_embed
    elif provider == "openai":
        try:
            embedder = OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            embedder = _mock_embed
    else:
        embedder = _mock_embed

    print(f"\nEmbedding backend: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")

    store = EmbeddingStore(collection_name="manual_test_store", embedding_fn=embedder)
    chunked_docs = chunk_documents(docs)
    if len(chunked_docs) != len(docs):
        print(f"\nChunked documents: {len(docs)} -> {len(chunked_docs)}")
    store.add_documents(chunked_docs)

    print(f"\nStored {store.get_collection_size()} documents in EmbeddingStore")
    print("\n=== EmbeddingStore Search Test ===")
    print(f"Query: {query}")
    search_results = store.search(query, top_k=3)
    for index, result in enumerate(search_results, start=1):
        print(f"{index}. score={result['score']:.3f} source={result['metadata'].get('source')}")
        print(f"   content preview: {result['content'][:120].replace(chr(10), ' ')}...")

    print("\n=== KnowledgeBaseAgent Test ===")
    llm_fn = demo_llm
    if provider == "openai":
        llm_fn = build_openai_llm()
    agent = KnowledgeBaseAgent(store=store, llm_fn=llm_fn)
    print(f"Question: {query}")
    print("Agent answer:")
    print(agent.answer(query, top_k=3))
    return 0


def main() -> int:
    question = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else None
    return run_manual_demo(question=question)


if __name__ == "__main__":
    raise SystemExit(main())
