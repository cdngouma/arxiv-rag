# Project Structure — arxiv-rag

**Repository:** https://github.com/cdngouma/arxiv-rag  
**Reference:** `main` branch, inspected 2026-10-15  

This document lists the repository structure and describes the **intended responsibility** of each component.

## Repository tree

```text
arxiv-rag/
├── .gitignore
├── README.md
├── app.py
├── pyproject.toml
├── notebooks/
│   └── archived.ipynb
└── src/
    └── research_rag/
        ├── __init__.py
        ├── api.py
        ├── assistant.py
        ├── config.py
        ├── schemas.py
        ├── evaluation/
        │   ├── evaluate.py
        │   └── metrics.py
        ├── ingestion/
        │   ├── arxiv.py
        │   ├── crossref.py
        │   ├── normalization.py
        │   └── semantic_scholar.py
        ├── ranking/
        │   ├── cross_encoder.py
        │   ├── integrity.py
        │   └── temporal.py
        └── retrieval/
            ├── bm25.py
            ├── dense.py
            ├── fusion.py
            └── hybrid.py
```

## Root and package files

| Path | Responsibility |
|---|---|
| `.gitignore` | Exclude local environments, caches, secrets, and generated artifacts from version control. |
| `README.md` | Public project overview, setup guidance, methodology, and reported results; should be updated as the rebuild progresses. |
| `app.py` | Potential top-level application launcher or demo entry point. Define a clear role or remove if `research_rag/api.py` becomes the only entry point. |
| `pyproject.toml` | Python package metadata, dependencies, development tools, and build configuration. |
| `notebooks/` | Exploratory analysis and experimental notebooks, kept separate from production package code. |
| `notebooks/archived.ipynb` | Retained prototype/legacy notebook for reference; not the authoritative implementation or evaluation. |
| `src/` | Source-layout root for the installable Python package. |
| `src/research_rag/` | Main application package, containing domain models and pipeline modules. |
| `src/research_rag/__init__.py` | Marks the package and optionally exposes a small public API. |
| `src/research_rag/api.py` | Intended HTTP interface, such as FastAPI endpoints for search and grounded answers. |
| `src/research_rag/assistant.py` | Orchestrate grounded answer generation using retrieved papers, context assembly, model prompting, and cited responses. |
| `src/research_rag/config.py` | Centralized runtime and model configuration, including retrieval/index paths and generation settings. |
| `src/research_rag/schemas.py` | Shared typed contracts for papers, identifiers, retrieval results, ranked results, and query constraints; avoids inconsistent objects across modules. |

## Ingestion

**Directory:** `src/research_rag/ingestion/` — obtains external research metadata and transforms it into consistent local records. Provider adapters should fetch/parse; normalization should reconcile provider differences.

| File | Responsibility |
|---|---|
| `arxiv.py` | Read arXiv metadata snapshots or API records, select the corpus, and extract identifiers, titles, abstracts, categories, and submission/update dates. |
| `semantic_scholar.py` | Batch-enrich paper records with Semantic Scholar identifiers, citations, publication information, and other available fields; handle caching, missing records, and rate limits. |
| `crossref.py` | Enrich DOI-linked records with Crossref publication metadata and correction/retraction information; preserve source provenance. |
| `normalization.py` | Normalize and reconcile provider records into the shared `Paper` schema, resolve duplicate identifiers and field conflicts, and track provenance. |

## Retrieval

**Directory:** `src/research_rag/retrieval/` — finds candidate papers based on lexical and semantic relevance. This stage should not conflate relevance with citation counts or integrity status.

| File | Responsibility |
|---|---|
| `bm25.py` | Build/load a lexical index and return BM25-ranked candidate papers for a query. |
| `dense.py` | Build/load an embedding-based FAISS index and retrieve semantically similar candidate papers. |
| `fusion.py` | Implement rank-fusion algorithms, principally reciprocal rank fusion (RRF), to merge ranked candidate lists without mixing incomparable raw scores. |
| `hybrid.py` | Orchestrate BM25 and dense retrieval, apply eligible candidate constraints where appropriate, and invoke `fusion.py` to produce one candidate set. |

## Ranking

**Directory:** `src/research_rag/ranking/` — refines candidate ordering and applies research-specific policies. Hard eligibility constraints may need to be enforced before ranking; module location does not dictate execution order.

| File | Responsibility |
|---|---|
| `cross_encoder.py` | Score query–paper pairs with a cross-encoder to improve semantic relevance ordering over first-stage retrieval. |
| `temporal.py` | Interpret date-constrained, recent, and foundational queries; enforce hard date limits and apply soft query-aware recency preferences. |
| `integrity.py` | Interpret retraction/correction/concern metadata and decide whether papers should be excluded, demoted, or flagged, depending on the query and policy. Does **not** fetch Crossref data. |

## Evaluation

**Directory:** `src/research_rag/evaluation/` — measures retrieval and ranking quality with independently judged relevance labels and reproducible experiments.

| File | Responsibility |
|---|---|
| `metrics.py` | Compute or wrap nDCG@k, Recall@k, MRR@k, and complementary quality/coverage measures with consistent definitions. |
| `evaluate.py` | Load benchmark queries and judgments, run retrieval/ranking variants, compare baselines and ablations, and save reproducible results. |

## Recommended additions

The following directories are recommended for the intended project, but are not part of the tree shown above:

| Path | When / why to add |
|---|---|
| `tests/` | Add immediately when implementing schemas and ingestion; include tests for ID reconciliation, date handling, fusion, and integrity policies. |
| `scripts/` | Add when ingestion, indexing, or benchmark workflows need repeatable CLI entry points. |
| `data/` | Add for local data conventions, sample fixtures, and relevance judgments. Keep large corpora and generated indexes out of Git; Git does not track empty directories. |
| `.github/workflows/` | Add when automated linting and tests are ready. |
| `docs/` | Optional; add only if architecture/methodology details outgrow the README and this document. |

## Architectural boundaries

1. **`schemas.py` defines contracts; `ingestion/normalization.py` constructs and reconciles records against those contracts.**
2. **`retrieval/fusion.py` implements fusion mathematics; `retrieval/hybrid.py` coordinates retrievers.**
3. **`ingestion/crossref.py` retrieves integrity-related facts; `ranking/integrity.py` applies query-aware policies to those facts.**
4. **`ranking/temporal.py` distinguishes hard date filters from soft recency preferences.**
5. **`evaluation/` must use independently judged relevance labels**, not labels generated by the same retriever under evaluation.
6. **`assistant.py` consumes retrieval/ranking results** and should not reimplement their scoring logic.


