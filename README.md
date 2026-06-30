# Metadata-Aware Research Paper Retrieval System

A metadata-aware Retrieval-Augmented Generation (RAG) system for research paper discovery and grounded question answering over arXiv papers.

Unlike conventional RAG systems that rank documents solely by semantic similarity, this project incorporates publication metadata to improve retrieval quality by prioritizing:

- Semantic relevance
- Publication recency
- Publication maturity (peer-review signals)

The goal is to emulate how researchers search for literature: retrieving papers that are not only relevant, but also recent and more likely to represent mature scientific work.

---

## Motivation

Semantic vector search often retrieves highly similar papers regardless of publication date or publication status.

For rapidly evolving fields such as Artificial Intelligence, users frequently prefer recent and peer-reviewed work over older preprints when semantic relevance is comparable.

This project introduces a lightweight metadata-aware reranking stage that refines semantic retrieval without overriding it.

---

## Features

- Semantic retrieval using FAISS and OpenAI embeddings
- Metadata-aware reranking
    - publication year
    - publication signals (`doi`, `journal-ref`)
- Local answer generation using Ollama
- Synthetic query generation
- Group-based retrieval evaluation
- Modular production-oriented architecture

---

## Retrieval Strategy

Candidate papers are first retrieved using semantic similarity.

Metadata is then used only to reorder already relevant papers.

Ranking priority:

```text
Semantic Relevance
        ↓
     Recency
        ↓
Publication Signal
```

Final ranking score:

```math
\text{FinalScore}
=
w_sS
+
w_rR
+
w_pP
```

where

- **S** = semantic similarity
- **R** = normalized recency score
- **P** = publication signal

This prevents metadata from dominating semantic relevance while still promoting newer and more credible research.

---

## Architecture

```text
                 User Query
                      │
                      ▼
           OpenAI Embedding Model
                      │
                      ▼
             FAISS Vector Search
                      │
                      ▼
          Metadata-aware Reranking
      (recency + publication signal)
                      │
                      ▼
          Top-k Grounding Context
                      │
                      ▼
             Ollama Local LLM
                      │
                      ▼
               Generated Answer
```

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

**Source**

- arXiv Metadata Snapshot

**Corpus**

- Categories:
    - `cs.AI`
    - `cs.CL`
    - `cs.LG`
    - `stat.ML`
- Publication years: **2020–2026**
- Stratified sample of **50,000 papers**

---

## Retrieval Pipeline

1. Embed the user query
2. Retrieve candidate papers using FAISS
3. Normalize semantic similarity scores
4. Apply metadata-aware reranking
5. Construct grounded retrieval context
6. Generate the final answer with Ollama

---

## Evaluation

Rather than evaluating only answer generation, this project evaluates retrieval quality directly.

Synthetic research queries are generated from held-out papers and evaluated over the full corpus.

Metrics include:

- **Group Hit@10**
- **Group Recall@10**
- **Group MRR@10**
- **Seed Hit@10**
- **Freshness@10**
- **Published Rate@10**

Together these metrics measure both retrieval quality and the ability to surface recent, publication-backed research.

---

## Results

| Configuration | Group Recall@10 | Group MRR@10 | Freshness@10 | Published Rate@10 |
|---|---:|---:|---:|---:|
| Baseline Semantic Search | 0.399 | 0.889 | 2023.70 | 0.243 |
| Metadata-aware Reranking | 0.388 | 0.904 | 2023.99 | 0.363 |

Although semantic recall decreases slightly, reranking substantially improves ranking quality while retrieving newer papers with stronger publication signals.

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

## Future Work

- Cross-encoder reranking
- Hybrid BM25 + dense retrieval
- Streamlit interface
- FastAPI inference service
- Human-labeled retrieval benchmark
