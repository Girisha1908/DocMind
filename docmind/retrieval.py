"""Retrieval strategies. Every strategy is just `retrieve(name, question, k) -> list[Document]`."""

import re
from dataclasses import dataclass
from functools import cache

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from .config import CANDIDATES, TOP_K
from .index import chunks, store
from .models import reranker


@dataclass(frozen=True)
class Strategy:
    name: str
    chunker: str
    mode: str  # mmr | vector | hybrid | rerank
    label: str


STRATEGIES = {
    s.name: s
    for s in [Strategy("s0_original", "recursive_1000", "mmr", "Original DocMind: 1000/200 chars + MMR")]
    + [
        Strategy(f"{chunker}+{mode}", chunker, mode, f"{label} + {mode_label}")
        for chunker, label in [("fixed_500", "Fixed 500-token"), ("semantic", "Semantic"), ("headers", "Header-aware")]
        for mode, mode_label in [("vector", "vector"), ("hybrid", "hybrid BM25+vector (RRF)"), ("rerank", "hybrid + cross-encoder rerank")]
    ]
}


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


@cache
def _bm25(chunker: str) -> BM25Retriever:
    return BM25Retriever.from_documents(chunks(chunker), k=CANDIDATES, preprocess_func=_tokens)


def _rrf(*rankings: list[Document], c: int = 60) -> list[Document]:
    """Reciprocal Rank Fusion: score = sum 1/(c + rank). No score normalisation, no tuned weights."""
    scores, docs = {}, {}
    for ranking in rankings:
        for rank, d in enumerate(ranking):
            key = d.metadata["chunk_id"]
            scores[key] = scores.get(key, 0) + 1 / (c + rank + 1)
            docs[key] = d
    return [docs[k] for k in sorted(scores, key=scores.get, reverse=True)]


def _hybrid(chunker: str, question: str) -> list[Document]:
    vector = store(chunker).similarity_search(question, k=CANDIDATES)
    return _rrf(vector, _bm25(chunker).invoke(question))[:CANDIDATES]


def retrieve(name: str, question: str, k: int = TOP_K) -> list[Document]:
    s = STRATEGIES[name]
    if s.mode == "mmr":
        # MMR picks greedily, so the first k of k=5 equal a k=3 run with the same fetch_k
        return store(s.chunker).max_marginal_relevance_search(question, k=k, fetch_k=10, lambda_mult=0.5)
    if s.mode == "vector":
        return store(s.chunker).similarity_search(question, k=k)
    candidates = _hybrid(s.chunker, question)
    if s.mode == "hybrid":
        return candidates[:k]
    scores = list(reranker().rerank(question, [d.page_content for d in candidates]))
    ranked = sorted(zip(scores, range(len(candidates))), reverse=True)
    return [candidates[i] for _, i in ranked[:k]]
