"""One Chroma collection per chunker, persisted under chroma_db/ (a build artifact, rebuilt by scripts/build_index.py)."""

from functools import cache

from langchain_chroma import Chroma
from langchain_core.documents import Document

from .chunking import CHUNKERS
from .config import INDEX_DIR
from .corpus import load_corpus
from .models import embeddings


def store(chunker: str) -> Chroma:
    return Chroma(
        collection_name=chunker,
        embedding_function=embeddings(),
        persist_directory=str(INDEX_DIR),
        collection_metadata={"hnsw:space": "cosine"},
    )


def build(chunker: str, docs: list[Document] | None = None) -> int:
    chunks = CHUNKERS[chunker](docs or load_corpus())
    for i, c in enumerate(chunks):
        c.metadata["chunk_id"] = f"{chunker}:{i}"
    db = store(chunker)
    db.reset_collection()
    db.add_documents(chunks, ids=[c.metadata["chunk_id"] for c in chunks])
    return len(chunks)


@cache
def chunks(chunker: str) -> list[Document]:
    """All chunks of a collection, in build order (for BM25)."""
    got = store(chunker).get(include=["documents", "metadatas"])
    if not got["ids"]:
        raise RuntimeError(f"Index '{chunker}' is empty. Run: python scripts/build_index.py")
    pairs = sorted(zip(got["ids"], got["documents"], got["metadatas"]), key=lambda x: int(x[0].split(":")[1]))
    return [Document(page_content=t, metadata=m) for _, t, m in pairs]
