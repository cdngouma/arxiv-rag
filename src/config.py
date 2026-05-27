from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "raw" / "arxiv-metadata-oai-snapshot.json"
INDEX_DIR = BASE_DIR / "indexes"
FAISS_INDEX_NAME = "arxiv_index"

TARGET_CATEGORIES = {"cs.AI", "cs.CL", "cs.LG", "stat.ML"}

MIN_YEAR = 2020
MAX_YEAR = 2026

SAMPLE_SIZE = 50_000
RANDOM_STATE = 42

K = 10
FETCH_K = 30
RERANK = True

W_VECTOR = 0.80
W_RECENCY = 0.10
W_PUBLICATION = 0.10

EMBEDDING_MODEL = OpenAIEmbeddings(model="text-embedding-3-small")