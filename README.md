# DocMind: RAG with a measured accuracy number

[![Retrieval eval](https://github.com/Girisha1908/DocMind/actions/workflows/eval.yml/badge.svg)](https://github.com/Girisha1908/DocMind/actions/workflows/eval.yml)

DocMind answers employee questions from a company handbook: leave, benefits, expenses, travel and onboarding. It retrieves the three most relevant passages and has an LLM answer from those passages only, citing them.

Most RAG demos stop there. This one also measures how often retrieval finds the right passage. It compares ten retrieval strategies on a hand-checked set of 50 questions, and CI fails the build if accuracy drops.

> **Why it matters:** if retrieval returns the wrong passage, the model still writes a confident, fluent, wrong answer. You only catch that by measuring retrieval on its own.

## Results

<!-- RESULTS:START -->
_Pending first full run. Generate with `python eval/run_retrieval.py`; the table is written to `results/latest.md`._
<!-- RESULTS:END -->

**How to read it:** Hit@3 is the share of answerable questions where a chunk containing the gold evidence lands in the top 3 results, which is exactly what the LLM gets to see. MRR@5 rewards putting it at rank 1 rather than rank 3.

## How it works

```
                 ┌──────────── offline (scripts/build_index.py) ────────────┐
corpus/*.md ──►  chunker (1 of 4) ──► bge-small embeddings ──► Chroma collection
                                    └──────────────► BM25 index (in memory)

question ──► retrieve(strategy) ──► top 3 chunks ──► Mistral Small ──► answer with [1][2] citations
                   │
                   ├─ vector:  cosine similarity in Chroma
                   ├─ hybrid:  BM25 top 20 + vector top 20, fused with Reciprocal Rank Fusion
                   └─ rerank:  hybrid top 20, re-scored by a cross-encoder, keep 3
```

### The corpus

There are 46 pages of the public [GitLab Handbook](https://handbook.gitlab.com) (about 880 KB of text), pinned to commit `29350f82`:

- Leave and time off, including parental leave
- Total rewards: compensation, equity, incentives, and 21 country benefit pages
- The global travel and expense policy
- Onboarding and offboarding
- Relocation and visas
- Probation, promotions, anti-harassment, and acceptable use

It's real company policy text, written by many authors and messy. The country benefit pages are near-duplicates of each other: "parental leave in the UK" and "parental leave in the Netherlands" are separate pages that share most of their vocabulary. That makes naive retrieval fail in realistic ways.

`scripts/fetch_corpus.py` downloads the snapshot through the GitLab API and strips front matter, Hugo shortcodes, HTML and link targets. The cleaned files are committed, so the eval never depends on the network. The content is CC BY-SA 4.0; see [corpus/NOTICE.md](corpus/NOTICE.md).

### Chunking strategies

All four use the same embedding model, so chunking is the only variable.

| Chunker | What it does | Why it's here |
|---|---|---|
| `recursive_1000` | 1000 characters, 200 overlap, splits on paragraph and line breaks | The original DocMind setup: the "before" number |
| `fixed_500` | Fixed windows of 500 tokens with 64 overlap, counted with the embedder's own tokenizer. It ignores headings and sentences | The textbook naive baseline |
| `semantic` | Embeds every sentence and splits where the distance between neighbouring sentences is above the 95th percentile (LangChain `SemanticChunker`). Pieces are capped at 500 tokens | "Semantic chunking" as usually described |
| `headers` | Splits on markdown `#`/`##`/`###`, then recursively to 500 tokens, and prefixes each chunk with its heading path (`Leave Types > Parental Leave`) | Uses the document's own structure |

The 500-token cap exists because `bge-small` reads at most 512 tokens. Anything longer would be silently truncated at embedding time, so the end of the chunk would be invisible to vector search.

### Retrieval modes

| Mode | How |
|---|---|
| `mmr` | Maximal Marginal Relevance (fetch 10, λ=0.5). Used only by the original-setup row |
| `vector` | Top-k by cosine similarity in Chroma |
| `hybrid` | BM25 (lower-cased word tokens) and vector search each return 20 results, merged with **Reciprocal Rank Fusion** (k=60). RRF combines ranks, not scores, so BM25 and cosine scores never need normalising, and there are no weights to tune (and so no way to overfit them to the test questions) |
| `rerank` | The hybrid top 20, re-scored by the cross-encoder `ms-marco-MiniLM-L-6-v2`, which reads the question and each passage together. Keeps the top 3 |

That gives 1 baseline + 3 chunkers × 3 modes = **10 strategies** in the matrix. The headline "ladder" is:

1. Original setup
2. Simple chunking (`fixed_500+vector`)
3. Semantic chunking (`semantic+vector`)
4. Hybrid search on the best-scoring chunker
5. Reranking on the best-scoring chunker

The ladder picks the best chunker from the vector-only scores, so the choice is reproducible rather than hand-picked.

### Models

All retrieval models run locally on CPU through ONNX (fastembed), with no API key. That's what lets CI run for free.

- Embeddings: `BAAI/bge-small-en-v1.5` (384 dimensions)
- Reranker: `Xenova/ms-marco-MiniLM-L-6-v2` (80 MB)
- Answers: Mistral `mistral-small-2506`, temperature 0
- Judge (answer eval only): `mistral-large-latest`

## Evaluation

### The answer key

[`eval/questions.jsonl`](eval/questions.jsonl) has 50 questions, described in detail in [eval/README.md](eval/README.md):

| Type | Count | What it tests |
|---|---|---|
| direct | 20 | Ordinary questions |
| paraphrase | 15 | Wording that avoids the answer's key terms, which favours vector search |
| exact_term | 8 | Vendor names, acronyms and figures, which favour BM25 |
| unanswerable | 7 | Not in the handbook; the bot should decline |

Each answerable question stores a short **evidence span** copied word for word from its source page. A retrieved chunk is a hit if it comes from the right file and contains the span. Matching tolerates whitespace and markdown differences, and a span cut by a chunk boundary still counts if at least 80% of it survives.

Gold labels are text rather than chunk IDs. That's what allows one answer key to grade every chunking strategy fairly.

### Two layers of evaluation

| | Retrieval eval | Answer eval |
|---|---|---|
| Script | `eval/run_retrieval.py` | `eval/run_answers.py` |
| Question | Did the right passage reach the LLM? | Is the final answer correct? |
| Metrics | Hit@1/3/5, MRR@5, Hit@3 per question type, latency | correct / partial / wrong / abstained, and abstentions on the 7 unanswerable questions |
| Cost | Free, deterministic, ~minutes | Mistral API calls |
| Runs in CI | Yes | No (local) |

The answer eval uses Mistral Large to judge Mistral Small, so the model isn't grading itself. It also writes 10 random answers to `eval/human_grades.csv` for you to grade by hand. `--agreement` then reports how often you and the judge agree, which is the answer to "how do you know the judge is right?"

### CI quality gate

[`.github/workflows/eval.yml`](.github/workflows/eval.yml) runs on every push to `main` and every pull request:

1. Install dependencies and restore the cached models.
2. `pytest tests/`: every evidence span still exists in the corpus.
3. Build all four indexes from scratch.
4. `run_retrieval.py --check`, which fails the build if either:
   - the production strategy's Hit@3 is below `min_hit_at_3` in [`eval/thresholds.yaml`](eval/thresholds.yaml), or
   - any strategy's Hit@3 drops more than `max_regression_pp` (3 points) below [`results/baseline.json`](results/baseline.json).
5. Post the results table as a PR comment and job summary, and upload the JSON as an artifact.

The floor was set at the first full measurement minus 5 points. Lowering it takes a commit to `thresholds.yaml`, so it shows up in review.

## Running it

Requires Python 3.12+ (developed on 3.14).

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
```

Build the indexes once. This downloads about 200 MB of models on the first run:

```bash
python scripts/build_index.py
```

Retrieval eval, which needs no API key:

```bash
python eval/run_retrieval.py
```

Answer generation needs a Mistral key (the free tier is enough). Create `.env`:

```env
MISTRAL_API_KEY=your_key_here
```

```bash
streamlit run app.py                # web app: strategy picker, cited sources, upload-your-own-PDF mode
python main.py                      # terminal chat
python eval/run_answers.py          # answer-quality eval with LLM judge
```

Without a key, the app still runs and shows the retrieved passages.

Updating the baseline after an intentional change, e.g. editing questions:

```bash
python eval/run_retrieval.py --save-baseline
```

## Project layout

```
docmind/            the pipeline, shared by app.py, main.py and the evals
  corpus.py         load corpus/ into Documents with title + handbook URL
  chunking.py       the four chunkers
  index.py          one Chroma collection per chunker
  retrieval.py      every strategy as retrieve(name, question, k)
  generate.py       Mistral answer with citations and an abstain phrase
  models.py         local ONNX embedder, tokenizer, reranker
corpus/             46 cleaned handbook pages (CC BY-SA 4.0) + NOTICE.md
eval/
  questions.jsonl   the 50-question answer key
  run_retrieval.py  retrieval metrics + CI gate
  run_answers.py    answer quality with LLM judge + human agreement
  thresholds.yaml   CI floor and allowed regression
results/            latest.json/.md (each run), baseline.json (committed reference)
scripts/            fetch_corpus.py, build_index.py
tests/              answer-key integrity checks
docs/               DESIGN.md and the Google Stitch UI prompt
notebooks/scratch/  early LangChain experiments (loaders, MMR, multi-query)
```

## Design decisions

- **Chroma over PGVector.** It's embedded, with no server to run, and the indexes rebuild from scratch in CI. PGVector becomes worth it when the vectors need to live next to transactional data.
- **Local ONNX models over API embeddings.** They cost nothing, need no secrets in CI, and give reproducible numbers.
- **One embedding model for every strategy.** Otherwise the comparison would be measuring the embedder, not the strategy.
- **k = 3 everywhere.** The metric matches exactly what the LLM sees.
- **Unanswerable questions are excluded from Hit@k.** There's nothing to retrieve, so they're scored as abstentions in the answer eval instead. That's why the denominator is 43, not 50.
- **No tuning on the test set.** Chunk sizes, RRF k and candidate counts are standard defaults chosen before the first run. With only 50 questions, tuning on them would mostly measure noise.

## Limitations

- 43 answerable questions is a small sample. One question is worth about 2.3 points of Hit@3, so differences under about 5 points between strategies are within noise.
- The questions were drafted with AI assistance against known passages and are being reviewed and partly rewritten by hand. That's tracked per question in `author` and `reviewed_by_human`.
- Hit@3 measures whether the evidence was retrieved, not whether the answer was right. The answer eval covers that, but it relies on an LLM judge, which the human-agreement check calibrates.
- The corpus is a snapshot. Real handbook pages change, so the answer key is tied to commit `29350f82`.

## Credits

- Handbook content © GitLab Inc., [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
- Code: MIT, see [LICENSE](LICENSE).
