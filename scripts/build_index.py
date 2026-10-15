"""Chunk the corpus with every chunker and (re)build its Chroma collection.

    python scripts/build_index.py              # all chunkers
    python scripts/build_index.py headers      # just one
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from docmind.chunking import CHUNKERS  # noqa: E402
from docmind.corpus import load_corpus  # noqa: E402
from docmind.index import build  # noqa: E402


def main() -> None:
    names = sys.argv[1:] or list(CHUNKERS)
    docs = load_corpus()
    print(f"{len(docs)} documents")
    for name in names:
        t = time.perf_counter()
        n = build(name, docs)
        print(f"{name:<15} {n:>5} chunks  {time.perf_counter() - t:5.1f}s")


if __name__ == "__main__":
    main()
