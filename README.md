# Recency-Aware Research Paper RAG Assistant

A metadata-aware Retrieval-Augmented Generation (RAG) system for research-paper discovery and question answering over arXiv papers.

The system combines semantic vector retrieval with metadata-aware reranking to prioritize:
1. Semantic relevance
2. Recency
3. Publication maturity

The project focuses on realistic research-assistant retrieval behavior rather than generic chatbot interaction.

---

## Features

- Semantic retrieval using FAISS + OpenAI embeddings
- Metadata-aware reranking
    - publication year
    - publication signal (`doi` / `journal-ref`)
- Local LLM inference using Ollama
- Group-based retrieval evaluation
- Synthetic query generation for benchmarking
- Production-oriented modular architecture

---

## Retrieval Objective

The ranking system follows the hierarchy:

$$
\text{Semantic Relevance}
\; > \;
\text{Recency}
\; > \;
\text{Publication Signal}
$$

Metadata signals are used to refine rankings among already relevant papers rather than override semantic similarity.

---

## Project Structure

```text
project/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── indexes/
│
├── notebooks/
│   ├── 01_data_preparation.ipynb
│   ├── 02_retrieval_evaluation.ipynb
│   └── 03_generation_evaluation.ipynb
│
├── src/
│   ├── assistant.py
│   ├── config.py
│   ├── data_loader.py
│   └── retriever.py
│
├── requirements.txt
└── README.md
```

---

## Dataset

Source:
- arXiv Metadata Snapshot

Corpus filtering:
- Categories: `cs.AI`, `cs.CL`, `cs.LG`, `stat.ML`
- Years: `2020–2026`
- Stratified sampling: `50,000` papers

---

## Retrieval Pipeline

1. Retrieve candidate papers using FAISS semantic search
2. Normalize vector similarity scores
3. Apply metadata-aware reranking
4. Build grounded LLM context
5. Generate answer using local LLM

Final ranking score:

$$
\text{FinalScore}
=
(w_{vector} \times VectorScore)
+
(w_{recency} \times RecencyScore)
+
(w_{publication} \times PublicationScore)
$$

---

## Evaluation

The project uses a group-based retrieval benchmark:
- synthetic research queries
- semantic relevance groups
- full-corpus retrieval evaluation

Metrics:
- **Group Hit@10**: proportion of queries where at least one paper from the relevant semantic group appears in the top-10 retrieved results.
- **Group Recall@10**: proportion of the relevant semantic paper group retrieved within the top-10 results.
- **Group MRR@10**: reciprocal rank of the first retrieved paper belonging to the relevant semantic group, measuring ranking quality.
- **Seed Hit@10**: whether the original seed paper used to generate the query appears in the top-10 retrieved results.
- **Freshness@10**: average publication year of the top-10 retrieved papers, measuring recency preference.
- **Published Rate@10**: proportion of top-10 retrieved papers containing a publication signal (`doi` or `journal-ref`), measuring publication maturity.

The evaluation benchmark intentionally reflects recency-aware research retrieval behavior.

---

## Example Results

| Configuration | Group Recall@10 | Group MRR@10 | Freshness@10 | Published Rate@10 |
|---|---|---|---|---|
| Baseline Semantic Search | 0.399 | 0.889 | 2023.70 | 0.243 |
| Balanced Reranking | 0.388 | 0.904 | 2023.99 | 0.363 |

The balanced reranking configuration improved ranking quality, freshness, and publication maturity while preserving most semantic retrieval coverage.

---

## Tech Stack

- Python
- LangChain
- FAISS
- OpenAI Embeddings
- Ollama
- Pandas
- NumPy

---

## Future Improvements

- Streamlit interface
- FastAPI inference
- Human-labeled evaluation benchmark
```