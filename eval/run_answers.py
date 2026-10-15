"""Answer-quality eval (local only, costs Mistral API calls; not run in CI).

    python eval/run_answers.py                 # production strategy from eval/thresholds.yaml
    python eval/run_answers.py --strategy semantic+vector
    python eval/run_answers.py --agreement     # compare your grades in eval/human_grades.csv with the judge

Mistral Small answers each question from the top-3 chunks; Mistral Large grades the answer against the gold
answer as correct / partial / wrong / abstained. For unanswerable questions, abstaining is the correct outcome.
"""

import argparse
import csv
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from docmind.config import JUDGE_MODEL  # noqa: E402
from docmind.generate import ABSTAIN, answer, llm  # noqa: E402
from docmind.retrieval import retrieve  # noqa: E402

QUESTIONS = ROOT / "eval" / "questions.jsonl"
HUMAN = ROOT / "eval" / "human_grades.csv"
OUT = ROOT / "results" / "answers.jsonl"
GRADES = ["correct", "partial", "wrong", "abstained"]

JUDGE = """You grade an HR FAQ bot. Compare the BOT ANSWER with the GOLD ANSWER for the QUESTION.
Reply with exactly one word:
- correct: states the gold answer's key facts (extra correct detail is fine)
- partial: some key facts right, some missing or wrong
- wrong: contradicts or misses the gold answer, or answers a question that should have been declined
- abstained: the bot says it could not find the answer

QUESTION: {question}
GOLD ANSWER: {gold}
BOT ANSWER: {answer}
GRADE:"""


def judge(question: str, gold: str, bot: str) -> str:
    reply = llm(JUDGE_MODEL).invoke(JUDGE.format(question=question, gold=gold, answer=bot)).content.strip().lower()
    return next((g for g in GRADES if g in reply), "wrong")


def run(strategy: str) -> None:
    questions = [json.loads(l) for l in QUESTIONS.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = []
    for q in questions:
        bot = answer(q["question"], retrieve(strategy, q["question"]))
        grade = judge(q["question"], q["answer"], bot)
        if not q["evidence"] and (grade == "abstained" or ABSTAIN.lower() in bot.lower()):
            grade = "correct"  # declining an unanswerable question is the right behaviour
        rows.append({"id": q["id"], "type": q["type"], "question": q["question"], "gold": q["answer"], "answer": bot, "judge": grade})
        print(f"{q['id']} {grade:<9} {q['question'][:70]}")
        time.sleep(1.1)  # stay under the free tier's 1 request/second
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    answerable = [r for r in rows if r["type"] != "unanswerable"]
    unanswerable = [r for r in rows if r["type"] == "unanswerable"]
    counts = Counter(r["judge"] for r in answerable)
    print(f"\nstrategy: {strategy}")
    print(f"answer accuracy (answerable): {counts['correct']}/{len(answerable)} correct, {counts['partial']} partial, "
          f"{counts['wrong']} wrong, {counts['abstained']} wrongly abstained")
    print(f"abstention accuracy (unanswerable): {sum(r['judge'] == 'correct' for r in unanswerable)}/{len(unanswerable)}")

    if not HUMAN.exists():
        sample = random.Random(0).sample(rows, 10)
        with HUMAN.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, ["id", "question", "gold", "answer", "your_grade"])
            w.writeheader()
            w.writerows({k: r[k] for k in ["id", "question", "gold", "answer"]} | {"your_grade": ""} for r in sample)
        print(f"\nWrote {HUMAN.relative_to(ROOT)}: fill in your_grade ({'/'.join(GRADES)}), then run --agreement")


def agreement() -> None:
    judged = {r["id"]: r["judge"] for r in map(json.loads, OUT.read_text(encoding="utf-8").splitlines())}
    rows = [r for r in csv.DictReader(HUMAN.open(encoding="utf-8")) if r["your_grade"].strip()]
    same = sum(r["your_grade"].strip().lower() == judged[r["id"]] for r in rows)
    print(f"judge agrees with you on {same}/{len(rows)} answers")
    for r in rows:
        if r["your_grade"].strip().lower() != judged[r["id"]]:
            print(f"  {r['id']}: you={r['your_grade']} judge={judged[r['id']]}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default=yaml.safe_load((ROOT / "eval" / "thresholds.yaml").read_text())["production_strategy"])
    ap.add_argument("--agreement", action="store_true")
    args = ap.parse_args()
    agreement() if args.agreement else run(args.strategy)
