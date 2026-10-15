# Evaluation set

`questions.jsonl` is the answer key: 50 questions about the GitLab Handbook corpus in `../corpus/`.

| Type | Count | What it tests |
|---|---|---|
| `direct` | 20 | Natural questions that share some words with the answer |
| `paraphrase` | 15 | Everyday wording that avoids the answer's key terms ("time off when my baby arrives"). Vector search should beat BM25 here |
| `exact_term` | 8 | Questions that hinge on a vendor name, acronym or number ("SageView", "ESPP", "ISOS"). BM25 should beat vector search here |
| `unanswerable` | 7 | Plausible questions the handbook never answers. Scored only in the answer eval, where the bot should decline |

14 of the questions are about country benefit pages that are near-duplicates of each other (UK, Netherlands, Japan, Korea, …). Each question names its country, and only the right country's page counts as a hit.

## Record format

```json
{"id": "a01", "question": "How many weeks of paid parental leave does GitLab provide?",
 "type": "direct",
 "answer": "16 weeks, to be used before the child's first birthday or first anniversary of adoption",
 "evidence": ["GitLab provides 16 weeks of paid Parental Leave, which must be used prior to the child's first birthday or the first anniversary of the adoption."],
 "source": "people-group/time-off-and-absence/leave-types.md",
 "author": "claude-draft", "reviewed_by_human": false}
```

- `evidence` holds short spans copied word for word from `source`. A retrieved chunk counts as relevant if it comes from `source` and contains one of the spans. Matching ignores case, whitespace and markdown symbols, and still counts a hit when a chunk boundary cuts the span, as long as at least 80% of it is present.
- Because the gold label is a span of text, not a chunk ID, every chunking strategy is graded against the same key.
- `answer` is the gold answer used by the LLM judge in `run_answers.py`.
- `author` is `claude-draft` or `human`. `reviewed_by_human` is set to `true` once someone has checked the question, answer and span against the source page.

## How the set was built

1. Three drafting passes, each covering one part of the corpus (leave and rewards, country benefits, finance and people policies). Each evidence span was checked with an exact-substring search to confirm it appears only in its source file.
2. Each unanswerable question was checked against the whole corpus by searching for its key terms and synonyms, which are listed in `checked_terms`.
3. **Human review (to do):** check every question against its source page, rewrite at least 15 in your own words or replace them with your own, and set `author`/`reviewed_by_human`. Then re-run the eval and refresh the baseline (see the top-level README).

Run `python -m pytest tests/` to check that every span still matches its source file after any edit.

## Licence

The evidence spans are quotes from the GitLab Handbook and are licensed CC BY-SA 4.0 (see `../corpus/NOTICE.md`).
