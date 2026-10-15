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

RAG_MODEL = "gemma3:4b"
LLM_TEMPERATURE = 0.2
LLM_CONTEXT_WINDOW = 4096

MIN_VECTOR_SCORE = 0.3
MIN_RESULTS_AFTER_FILTER = 3

SYSTEM_PROMPT = """
You are an advanced academic research assistant. Answer the user query using ONLY the provided context below.

CRITICAL FALLBACK RULE:
If the provided context does not contain the explicit answer to the query, you MUST respond that the requested topic is not covered within the current arXiv machine learning corpus. Do NOT append any citations, bracketed text, or explanations if this happens.

STRICT STYLE & FORMATTING RULES (FOR VALID ANSWERS):
1. Introduce your response by logically connecting it to the terminology used in the user's query (e.g., if asked 'What are the breakthroughs in X?', start your first sentence with 'Some of the breakthroughs in X include...')
2. Absolute Ban on Document Meta-Language: Never use phrases like 'Based on the provided documents', 'According to the text', 'the context mentions', or 'the documents state'. Speak about the scientific facts directly as established truths.
3. Append your citation IDs between brackets (e.g., [arxiv.xxxx.xxxx]) smoothly at the end of clauses or sentences to validate your factual claims.
4. Prefer organizing your response with bullet points when appropriate.

"""