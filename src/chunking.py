from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        # Split sentences using regex for '.', '!', '?', or '.\n'
        # Keep the delimiter with the sentence
        sentences = re.split(r'(?<=[.!?])\s+|(?<=\.)\n', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = ' '.join(sentences[i:i+self.max_sentences_per_chunk])
            chunks.append(chunk.strip())
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case: if text is short enough or no separators left
        if len(current_text) <= self.chunk_size or not remaining_separators:
            return [current_text.strip()] if current_text.strip() else []
        sep = remaining_separators[0]
        if sep:
            pieces = current_text.split(sep)
        else:
            # If separator is empty string, split into chunk_size pieces
            return [current_text[i:i+self.chunk_size].strip() for i in range(0, len(current_text), self.chunk_size) if current_text[i:i+self.chunk_size].strip()]
        chunks = []
        buf = ""
        for piece in pieces:
            if buf:
                candidate = buf + sep + piece if sep else buf + piece
            else:
                candidate = piece
            if len(candidate) > self.chunk_size:
                if buf:
                    chunks.extend(self._split(buf, remaining_separators[1:]))
                buf = piece
            else:
                buf = candidate
        if buf:
            chunks.extend(self._split(buf, remaining_separators[1:]))
        return [c for c in chunks if c.strip()]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    # Cosine similarity: dot(a, b) / (||a|| * ||b||)
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        results = {}
        # FixedSizeChunker
        fixed = FixedSizeChunker(chunk_size=chunk_size)
        fixed_chunks = fixed.chunk(text)
        results['fixed_size'] = {
            'count': len(fixed_chunks),
            'avg_length': sum(len(c) for c in fixed_chunks) / len(fixed_chunks) if fixed_chunks else 0,
            'chunks': fixed_chunks,
            'preserves_context': True
        }
        # SentenceChunker
        sent = SentenceChunker(max_sentences_per_chunk=3)
        sent_chunks = sent.chunk(text)
        results['by_sentences'] = {
            'count': len(sent_chunks),
            'avg_length': sum(len(c) for c in sent_chunks) / len(sent_chunks) if sent_chunks else 0,
            'chunks': sent_chunks,
            'preserves_context': True
        }
        # RecursiveChunker
        rec = RecursiveChunker(chunk_size=chunk_size)
        rec_chunks = rec.chunk(text)
        results['recursive'] = {
            'count': len(rec_chunks),
            'avg_length': sum(len(c) for c in rec_chunks) / len(rec_chunks) if rec_chunks else 0,
            'chunks': rec_chunks,
            'preserves_context': True
        }
        return results
