"""Command-line chat over the GitLab Handbook.

    python main.py                          # production strategy
    python main.py --strategy fixed_500+vector
"""

import argparse

import yaml

from docmind.config import ROOT
from docmind.generate import answer
from docmind.retrieval import STRATEGIES, retrieve

production = yaml.safe_load((ROOT / "eval" / "thresholds.yaml").read_text())["production_strategy"]
ap = argparse.ArgumentParser()
ap.add_argument("--strategy", default=production, choices=list(STRATEGIES))
args = ap.parse_args()

print(f"DocMind ({STRATEGIES[args.strategy].label}). Press Enter on an empty line to exit.")
while question := input("\nYou: ").strip():
    docs = retrieve(args.strategy, question)
    print(f"\nAI: {answer(question, docs)}\n")
    for i, d in enumerate(docs, 1):
        print(f"  [{i}] {d.metadata['title']}  {d.metadata['url']}")
