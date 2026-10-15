"""Guards the answer key: every evidence span must still exist in its source file."""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = [json.loads(l) for l in (ROOT / "eval" / "questions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


def test_fifty_unique_questions():
    ids = [q["id"] for q in QUESTIONS]
    assert len(ids) == 50 and len(set(ids)) == 50


def test_evidence_spans_exist_in_source():
    for q in QUESTIONS:
        if q["type"] == "unanswerable":
            assert q["evidence"] == [] and q["source"] is None, q["id"]
            continue
        text = (ROOT / "corpus" / q["source"]).read_text(encoding="utf-8")
        for span in q["evidence"]:
            assert span in text, f"{q['id']}: span not found in {q['source']}: {span[:60]}"


def test_type_mix():
    assert set(Counter(q["type"] for q in QUESTIONS)) == {"direct", "paraphrase", "exact_term", "unanswerable"}
