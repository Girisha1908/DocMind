from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "corpus"
INDEX_DIR = ROOT / "chroma_db"
MODEL_CACHE = ROOT / ".cache" / "models"

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
RERANK_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"
ANSWER_MODEL = "mistral-small-2506"
JUDGE_MODEL = "mistral-large-latest"

TOP_K = 3            # chunks sent to the LLM, and the k in Hit@k
CANDIDATES = 20      # per-retriever pool for hybrid fusion and reranking
MAX_CHUNK_TOKENS = 500  # bge-small truncates at 512 tokens incl. special tokens

HANDBOOK_URL = "https://handbook.gitlab.com/handbook/"
