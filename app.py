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
mode = st.sidebar.radio("View", ["GitLab Handbook", "Upload your own PDF", "Evaluation results"])
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

elif mode == "Upload your own PDF":
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

else:
    import json
    import sys

    import pandas as pd

    sys.path.insert(0, str(ROOT / "eval"))
    from run_retrieval import ladder

    results = json.loads((ROOT / "results" / "latest.json").read_text())
    cfg = yaml.safe_load((ROOT / "eval" / "thresholds.yaml").read_text())
    prod = results[cfg["production_strategy"]]
    n = prod["n"]
    st.subheader("Retrieval evaluation")
    st.caption(f"{n} answerable questions (+7 unanswerable, scored separately). A hit means a chunk containing the "
               "gold evidence span was retrieved. Source: results/latest.json")

    c1, c2, c3, c4 = st.columns(4)
    base = results["s0_original"]["hit@3"]
    c1.metric(f"Hit@3 ({cfg['production_strategy']})", f"{prod['hit@3']:.1%}", f"{(prod['hit@3'] - base) * 100:+.1f} pp vs original")
    c2.metric("MRR@5", f"{prod['mrr@5']:.3f}")
    c3.metric("Hit@5", f"{prod['hit@5']:.1%}")
    passed = prod["hit@3"] >= cfg["min_hit_at_3"]
    c4.metric("CI gate", "passing" if passed else "failing", f"floor {cfg['min_hit_at_3']:.0%}", delta_color="off")

    st.markdown("**What each step added (Hit@3)**")
    steps = ladder(results)
    st.bar_chart(pd.DataFrame({"Hit@3 %": [results[s]["hit@3"] * 100 for _, s in steps]}, index=[label for label, _ in steps]),
                 horizontal=True, y_label="", x_label="Hit@3 (%)")

    st.markdown("**All strategies**")
    rows = [{"strategy": name, "Hit@1": r["hit@1"], "Hit@3": r["hit@3"], "Hit@5": r["hit@5"], "MRR@5": r["mrr@5"],
             **{f"Hit@3 {t}": v for t, v in r["by_type"].items()}, "ms/query": r["ms_per_query"]}
            for name, r in results.items()]
    df = pd.DataFrame(rows).sort_values("Hit@3", ascending=False).set_index("strategy")
    pct_cols = [c for c in df.columns if c.startswith("Hit")]
    st.dataframe(df.style.format({**{c: "{:.1%}" for c in pct_cols}, "MRR@5": "{:.3f}", "ms/query": "{:.0f}"})
                 .highlight_max(subset=pct_cols + ["MRR@5"], props="font-weight: bold"), width="stretch")

    st.markdown("**Hardest questions** (missed in the top 3 by most strategies)")
    lines = (ROOT / "eval" / "questions.jsonl").read_text(encoding="utf-8").splitlines()
    questions = {q["id"]: q for q in (json.loads(l) for l in lines if l.strip())}
    misses = {qid: sum(1 for r in results.values() if (r["ranks"].get(qid) or 99) > 3) for qid in prod["ranks"]}
    hard = sorted(misses.items(), key=lambda kv: -kv[1])[:8]
    st.dataframe(pd.DataFrame([{"id": q, "type": questions[q]["type"], "question": questions[q]["question"],
                                "missed by": f"{m}/{len(results)}"} for q, m in hard]).set_index("id"), width="stretch")
