import hashlib
import os
import tempfile

import streamlit as st
import yaml

from docmind.config import ROOT, TOP_K
from docmind.generate import answer
from docmind.retrieval import STRATEGIES, retrieve

st.set_page_config(page_title="DocMind", page_icon="📚")
st.title("📚 DocMind")

has_key = bool(os.getenv("MISTRAL_API_KEY"))
mode = st.sidebar.radio("Documents", ["GitLab Handbook", "Upload your own PDF"])
if not has_key:
    st.sidebar.warning("No MISTRAL_API_KEY in .env: showing retrieved passages only, no generated answer.")


def show(question: str, docs) -> None:
    if has_key:
        with st.spinner("Answering..."):
            st.markdown(answer(question, docs))
    st.caption(f"Top {len(docs)} retrieved passages")
    for i, d in enumerate(docs, 1):
        with st.expander(f"[{i}] {d.metadata.get('title', d.metadata.get('source'))}"):
            if "url" in d.metadata:
                st.markdown(f"[{d.metadata['url']}]({d.metadata['url']})")
            st.text(d.page_content)


if mode == "GitLab Handbook":
    production = yaml.safe_load((ROOT / "eval" / "thresholds.yaml").read_text())["production_strategy"]
    names = list(STRATEGIES)
    name = st.sidebar.selectbox(
        "Retrieval strategy", names, index=names.index(production),
        format_func=lambda n: f"{STRATEGIES[n].label}{'  (default)' if n == production else ''}",
    )
    st.write("Ask about GitLab's people policies, benefits, leave, expenses and travel.")
    question = st.text_input("Question", placeholder="What is the parental leave policy?")
    if question:
        show(question, retrieve(name, question))
    st.sidebar.caption("Content: GitLab Handbook, CC BY-SA 4.0")

else:
    from langchain_chroma import Chroma
    from langchain_community.document_loaders import PyPDFLoader

    from docmind.chunking import recursive_1000
    from docmind.models import embeddings

    uploaded = st.file_uploader("Upload a PDF", type="pdf")
    if uploaded:
        data = uploaded.getvalue()
        key = hashlib.sha256(data).hexdigest()
        if st.session_state.get("pdf_key") != key:
            with st.spinner("Indexing document..."), tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(data)
                f.close()
                pages = PyPDFLoader(f.name).load()
                for p in pages:
                    p.metadata["title"] = f"{uploaded.name}, page {p.metadata.get('page', 0) + 1}"
                st.session_state.pdf_store = Chroma.from_documents(recursive_1000(pages), embeddings(), collection_name=key[:32])
                st.session_state.pdf_key = key
                os.unlink(f.name)
        question = st.text_input("Question about your PDF")
        if question:
            show(question, st.session_state.pdf_store.similarity_search(question, k=TOP_K))
