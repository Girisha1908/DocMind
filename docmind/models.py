"""Local ONNX models (no API key, CPU-only), loaded once per process.

Speed notes (measured on a 4-core laptop CPU): cost is dominated by padding, because every text in a
batch is padded to the longest one and attention is quadratic in length. fastembed's defaults (batch 256,
input order, one ORT thread per logical core) were ~2x slower than length-sorted batches of 16 with
4 threads (= physical cores; hyperthread oversubscription made 8 threads slower still).
"""

from functools import cache

from langchain_core.embeddings import Embeddings

from .config import EMBED_MODEL, MODEL_CACHE, RERANK_MODEL

THREADS = 4      # onnxruntime intra-op threads: physical cores, not logical ones
EMBED_BATCH = 16
RERANK_BATCH = 8


def _by_length(texts: list[str]) -> list[int]:
    return sorted(range(len(texts)), key=lambda i: len(texts[i]))


class _SortedEmbeddings(Embeddings):
    """LangChain wrapper around fastembed that embeds in length-sorted batches and restores input order."""

    def __init__(self):
        from fastembed import TextEmbedding

        self.model = TextEmbedding(EMBED_MODEL, cache_dir=str(MODEL_CACHE), threads=THREADS)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        order = _by_length(texts)
        vectors = list(self.model.embed([texts[i] for i in order], batch_size=EMBED_BATCH))
        out: list[list[float]] = [[]] * len(texts)
        for i, v in zip(order, vectors):
            out[i] = v.tolist()
        return out

    def embed_query(self, text: str) -> list[float]:
        return next(iter(self.model.query_embed(text))).tolist()


class _SortedReranker:
    """fastembed TextCrossEncoder with length-sorted batches; rerank() returns scores in input order."""

    def __init__(self):
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        self.model = TextCrossEncoder(RERANK_MODEL, cache_dir=str(MODEL_CACHE), threads=THREADS)

    def rerank(self, query: str, documents: list[str]) -> list[float]:
        order = _by_length(documents)
        scores = list(self.model.rerank(query, [documents[i] for i in order], batch_size=RERANK_BATCH))
        out = [0.0] * len(documents)
        for i, s in zip(order, scores):
            out[i] = float(s)
        return out


@cache
def embeddings() -> Embeddings:
    return _SortedEmbeddings()


@cache
def tokenizer():
    from tokenizers import Tokenizer

    tok = Tokenizer.from_pretrained(EMBED_MODEL)
    tok.no_truncation()
    return tok


def count_tokens(text: str) -> int:
    return len(tokenizer().encode(text, add_special_tokens=False).ids)


@cache
def reranker() -> _SortedReranker:
    return _SortedReranker()
