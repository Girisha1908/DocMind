"""Four ways to cut the corpus into chunks. Each returns Documents carrying source/title/url metadata."""

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from .config import MAX_CHUNK_TOKENS
from .models import count_tokens, embeddings, tokenizer


def _with_meta(doc: Document, texts: list[str]) -> list[Document]:
    return [Document(page_content=t.strip(), metadata=dict(doc.metadata)) for t in texts if t.strip()]


def _token_splitter(size: int = MAX_CHUNK_TOKENS, overlap: int = 0) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap, length_function=count_tokens)


def recursive_1000(docs: list[Document]) -> list[Document]:
    """The original DocMind setup: 1000 characters, 200 overlap."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return [c for d in docs for c in _with_meta(d, splitter.split_text(d.page_content))]


def fixed_tokens(docs: list[Document], size: int = MAX_CHUNK_TOKENS, overlap: int = 64) -> list[Document]:
    """Naive baseline: fixed token windows that ignore headings, sentences and paragraphs."""
    out = []
    for d in docs:
        offsets = tokenizer().encode(d.page_content, add_special_tokens=False).offsets
        texts = []
        for start in range(0, len(offsets), size - overlap):
            window = offsets[start:start + size]
            texts.append(d.page_content[window[0][0]:window[-1][1]])
            if start + size >= len(offsets):
                break
        out += _with_meta(d, texts)
    return out


def semantic(docs: list[Document]) -> list[Document]:
    """Embedding-breakpoint chunking: split where adjacent sentences' embeddings diverge (95th percentile)."""
    from langchain_experimental.text_splitter import SemanticChunker

    chunker = SemanticChunker(
        embeddings(),
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=95,
        sentence_split_regex=r"(?<=[.?!])\s+|\n{2,}",  # sentences, plus markdown paragraph/list breaks
        min_chunk_size=400,  # characters, ~100 tokens
    )
    cap = _token_splitter()  # the embedder would silently truncate anything longer
    out = []
    for d in docs:
        texts = [piece for t in chunker.split_text(d.page_content) for piece in cap.split_text(t)]
        out += _with_meta(d, texts)
    return out


def headers(docs: list[Document]) -> list[Document]:
    """Structure-aware: split on #/##/### and prefix every chunk with its heading path."""
    md = MarkdownHeaderTextSplitter([("#", "h1"), ("##", "h2"), ("###", "h3")], strip_headers=True)
    out = []
    for d in docs:
        for section in md.split_text(d.page_content):
            path = " > ".join(v for k, v in sorted(section.metadata.items()))
            prefix = f"{path}\n\n" if path else ""
            body = _token_splitter(MAX_CHUNK_TOKENS - count_tokens(prefix), 50)
            out += _with_meta(d, [prefix + t for t in body.split_text(section.page_content)])
    return out


CHUNKERS = {
    "recursive_1000": recursive_1000,
    "fixed_500": fixed_tokens,
    "semantic": semantic,
    "headers": headers,
}
