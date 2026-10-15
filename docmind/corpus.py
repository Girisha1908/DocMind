from langchain_core.documents import Document

from .config import CORPUS_DIR, HANDBOOK_URL


def page_url(rel: str) -> str:
    path = rel.removesuffix(".md").removesuffix("_index").rstrip("/")
    return f"{HANDBOOK_URL}{path}/"


def load_corpus() -> list[Document]:
    docs = []
    for p in sorted(CORPUS_DIR.rglob("*.md")):
        if p.name == "NOTICE.md":
            continue
        rel = p.relative_to(CORPUS_DIR).as_posix()
        text = p.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip() if text.startswith("# ") else rel
        docs.append(Document(page_content=text, metadata={"source": rel, "title": title, "url": page_url(rel)}))
    return docs
