"""Retrieval eval: run every question through every strategy and score against the evidence spans.

    python eval/run_retrieval.py                  # all strategies -> results/latest.{json,md}
    python eval/run_retrieval.py --check          # also enforce eval/thresholds.yaml (CI)
    python eval/run_retrieval.py --save-baseline  # copy latest results to results/baseline.json

A retrieved chunk is relevant if it contains one of the question's evidence spans. Matching ignores case,
whitespace and markdown punctuation, and tolerates a span cut by a chunk boundary (>= 80% of it present
as one contiguous run). Unanswerable questions have no span and are excluded from retrieval metrics.
"""

import argparse
import json
import re
import shutil
import sys
import time
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from docmind.retrieval import STRATEGIES, retrieve  # noqa: E402

QUESTIONS = ROOT / "eval" / "questions.jsonl"
THRESHOLDS = ROOT / "eval" / "thresholds.yaml"
RESULTS = ROOT / "results"
DEPTH = 5  # retrieve top 5: Hit@1, Hit@3 (headline), Hit@5, MRR@5
MIN_COVERAGE = 0.8


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_`#>|\\]", " ", text.lower())).strip()


def contains(chunk: str, span: str) -> bool:
    chunk, span = normalize(chunk), normalize(span)
    if span in chunk:
        return True
    m = SequenceMatcher(None, span, chunk, autojunk=False).find_longest_match(0, len(span), 0, len(chunk))
    return m.size >= MIN_COVERAGE * len(span)


def load_questions() -> list[dict]:
    return [json.loads(line) for line in QUESTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]


def first_hit_rank(question: dict, docs) -> int | None:
    for rank, d in enumerate(docs, 1):
        if d.metadata["source"] == question["source"] and any(contains(d.page_content, e) for e in question["evidence"]):
            return rank
    return None


def score(ranks: dict[str, int | None]) -> dict:
    n = len(ranks)
    hit = lambda k: sum(r is not None and r <= k for r in ranks.values()) / n  # noqa: E731
    return {
        "hit@1": hit(1),
        "hit@3": hit(3),
        "hit@5": hit(5),
        "mrr@5": sum(1 / r for r in ranks.values() if r) / n,
        "n": n,
    }


def evaluate(questions: list[dict]) -> dict:
    answerable = [q for q in questions if q["evidence"]]
    results = {}
    for name, strategy in STRATEGIES.items():
        retrieve(name, "warm-up")  # load models and indexes outside the timer
        t = time.perf_counter()
        ranks = {q["id"]: first_hit_rank(q, retrieve(name, q["question"], DEPTH)) for q in answerable}
        ms = (time.perf_counter() - t) / len(answerable) * 1000
        by_type = defaultdict(dict)
        for q in answerable:
            by_type[q["type"]][q["id"]] = ranks[q["id"]]
        results[name] = {
            "label": strategy.label,
            "chunker": strategy.chunker,
            "mode": strategy.mode,
            **score(ranks),
            "by_type": {t: round(score(r)["hit@3"], 4) for t, r in sorted(by_type.items())},
            "ms_per_query": round(ms, 1),
            "ranks": ranks,
        }
        print(f"{name:<18} hit@3={results[name]['hit@3']:.1%}  mrr@5={results[name]['mrr@5']:.3f}  {ms:6.0f} ms/q")
    return results


def ladder(results: dict) -> list[tuple[str, str]]:
    """The 4-step story: baseline -> fixed -> semantic -> best chunker + hybrid -> + rerank."""
    best = max(["fixed_500", "semantic", "headers"], key=lambda c: (results[f"{c}+vector"]["hit@3"], results[f"{c}+vector"]["mrr@5"]))
    steps = [
        ("Original DocMind", "s0_original"),
        ("1. Simple chunking", "fixed_500+vector"),
        ("2. Semantic chunking", "semantic+vector"),
    ]
    if best == "headers":
        steps.append(("2b. Header-aware chunking", "headers+vector"))
    return steps + [
        (f"3. Hybrid search ({best} chunks)", f"{best}+hybrid"),
        (f"4. Reranking ({best} chunks)", f"{best}+rerank"),
    ]


def pct(x: float) -> str:
    return f"{x:.1%}"


def markdown(results: dict, questions: list[dict]) -> str:
    n = next(iter(results.values()))["n"]
    types = sorted({t for r in results.values() for t in r["by_type"]})
    lines = [
        f"## Retrieval accuracy ({n} answerable questions)\n",
        "| Step | Strategy | Hit@3 | MRR@5 |",
        "|---|---|---|---|",
    ]
    lines += [f"| {step} | `{name}` | **{pct(results[name]['hit@3'])}** | {results[name]['mrr@5']:.3f} |" for step, name in ladder(results)]
    lines += [
        "\n### All strategies\n",
        "| Strategy | Hit@1 | Hit@3 | Hit@5 | MRR@5 | " + " | ".join(f"Hit@3 {t}" for t in types) + " | ms/query |",
        "|---" * (6 + len(types)) + "|",
    ]
    for name, r in sorted(results.items(), key=lambda kv: -kv[1]["hit@3"]):
        cells = [pct(r["hit@1"]), f"**{pct(r['hit@3'])}**", pct(r["hit@5"]), f"{r['mrr@5']:.3f}"]
        cells += [pct(r["by_type"].get(t, 0)) for t in types]
        lines.append(f"| `{name}` | " + " | ".join(cells) + f" | {r['ms_per_query']:.0f} |")
    misses = defaultdict(list)
    for name, r in results.items():
        for qid, rank in r["ranks"].items():
            if rank is None or rank > 3:
                misses[qid].append(name)
    text = {q["id"]: q["question"] for q in questions}
    lines += ["\n### Hardest questions (missed in top 3 by most strategies)\n", "| id | question | strategies missing it |", "|---|---|---|"]
    for qid, names in sorted(misses.items(), key=lambda kv: -len(kv[1]))[:10]:
        lines.append(f"| {qid} | {text[qid]} | {len(names)}/{len(results)} |")
    return "\n".join(lines) + "\n"


def check(results: dict) -> list[str]:
    cfg = yaml.safe_load(THRESHOLDS.read_text())
    failures = []
    prod = cfg["production_strategy"]
    if results[prod]["hit@3"] < cfg["min_hit_at_3"]:
        failures.append(f"{prod}: Hit@3 {pct(results[prod]['hit@3'])} is below the floor {pct(cfg['min_hit_at_3'])}")
    baseline_path = RESULTS / "baseline.json"
    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text())
        for name, r in results.items():
            if name in baseline:
                drop = (baseline[name]["hit@3"] - r["hit@3"]) * 100
                if drop > cfg["max_regression_pp"]:
                    failures.append(f"{name}: Hit@3 dropped {drop:.1f} pp vs baseline ({pct(baseline[name]['hit@3'])} -> {pct(r['hit@3'])})")
    return failures


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if below thresholds or regressed vs baseline")
    ap.add_argument("--save-baseline", action="store_true", help="store these results as results/baseline.json")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles/pipes default to cp1252, which can't print ✅/❌

    questions = load_questions()
    results = evaluate(questions)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "latest.json").write_text(json.dumps(results, indent=2))
    report = markdown(results, questions)
    if args.check:
        failures = check(results)
        report += "\n### CI gate\n\n" + ("\n".join(f"- ❌ {f}" for f in failures) if failures else "- ✅ All thresholds met") + "\n"
    (RESULTS / "latest.md").write_text(report, encoding="utf-8")
    print("\n" + report)
    if args.save_baseline:
        shutil.copy(RESULTS / "latest.json", RESULTS / "baseline.json")
        print("saved results/baseline.json")
    if args.check and failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
