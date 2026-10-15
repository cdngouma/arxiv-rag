from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from src import config
from src.data_loader import load_preprocess_data


class ResearchPaperRetriever:
    """
    Handles research-paper document preparation, FAISS indexing,
    persistence, semantic retrieval, and metadata-aware reranking.
    """

    def __init__(self) -> None:
        self.embedding_model = config.EMBEDDING_MODEL
        self.index_dir = Path(config.INDEX_DIR)

        self.w_vector = config.W_VECTOR
        self.w_recency = config.W_RECENCY
        self.w_publication = config.W_PUBLICATION

        self.df: Optional[pd.DataFrame] = None
        self.documents: Optional[List[Document]] = None
        self.vectorstore: Optional[FAISS] = None

    def load_data(self) -> pd.DataFrame:
        self.df = load_preprocess_data(
            data_path=config.DATA_PATH,
            target_categories=config.TARGET_CATEGORIES,
            start_year=config.START_YEAR,
            end_year=config.END_YEAR,
            sample_size=config.SAMPLE_SIZE,
            random_state=config.RANDOM_STATE,
        )
        return self.df

    def _create_documents(self) -> List[Document]:
        """Convert processed dataframe rows into LangChain Documents."""
        if self.df is None:
            raise ValueError("No dataframe loaded. Call load_data() first.")

        documents: List[Document] = []

        for _, row in self.df.iterrows():
            metadata = {
                "id": row["id"],
                "title": row["title"],
                "year": int(row["year"]),
                "is_published": bool(row["is_published"]),
            }

            page_content = f"Title: {row['title']}\n\nAbstract: {row['abstract']}"

            documents.append(
                Document(
                    page_content=page_content,
                    metadata=metadata,
                )
            )

        self.documents = documents
        return self.documents

    def build_index(self) -> FAISS:
        """Build FAISS vectorstore from LangChain Documents."""
        if self.documents is None:
            self._create_documents()

        self.vectorstore = FAISS.from_documents(
            documents=self.documents,
            embedding=self.embedding_model,
        )

        return self.vectorstore

    def save_index(self) -> None:
        """Persist FAISS index locally."""
        if self.vectorstore is None:
            raise ValueError("No vectorstore available. Call build_index() first.")

        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.vectorstore.save_local(
            folder_path=str(self.index_dir),
            index_name=config.FAISS_INDEX_NAME,
        )

    def load_index(self) -> FAISS:
        """Load a persisted FAISS vectorstore."""
        self.vectorstore = FAISS.load_local(
            folder_path=str(self.index_dir),
            embeddings=self.embedding_model,
            index_name=config.FAISS_INDEX_NAME,
            allow_dangerous_deserialization=True,
        )

        return self.vectorstore

    def retrieve(
        self,
        query: str,
        k: int = config.K,
        fetch_k: int = config.FETCH_K,
        rerank: bool = config.RERANK,
    ):
        """
        Retrieve relevant papers using FAISS and optional metadata-aware reranking.
        """
        if self.vectorstore is None:
            raise ValueError("No vectorstore available.")

        docs_and_scores = self.vectorstore.similarity_search_with_score(
            query,
            k=fetch_k if rerank else k,
        )

        # Normalize FAISS distances into similarity-like scores
        raw_scores = [float(score) for _, score in docs_and_scores]
        min_score = min(raw_scores)
        max_score = max(raw_scores)

        results = []

        for doc, raw_score in docs_and_scores:
            raw_score = float(raw_score)

            # Smaller FAISS distance = better
            if max_score == min_score:
                vector_score = 1.0
            else:
                vector_score = 1.0 - (
                    (raw_score - min_score) / (max_score - min_score)
                )

            metadata = doc.metadata

            if rerank:
                recency_score = self._compute_recency_score(metadata["year"])
                publication_score = 1.0 if metadata["is_published"] else 0.0

                final_score = (
                    self.w_vector * vector_score
                    + self.w_recency * recency_score
                    + self.w_publication * publication_score
                )
            else:
                final_score = vector_score

            results.append({
                "id": metadata["id"],
                "title": metadata["title"],
                "year": metadata["year"],
                "is_published": metadata["is_published"],
                "content": doc.page_content,
                "vector_score": vector_score,
                "final_score": final_score,
            })

        results.sort(key=lambda x: x["final_score"], reverse=True)

        return results[:k]

    def _rerank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply semantic + recency + publication reranking."""
        for result in results:
            recency_score = self._compute_recency_score(result.get("year"))
            publication_score = 1.0 if result.get("is_published") else 0.0

            final_score = (
                self.w_vector * result["vector_score"]
                + self.w_recency * recency_score
                + self.w_publication * publication_score
            )

            result["recency_score"] = recency_score
            result["publication_score"] = publication_score
            result["final_score"] = final_score

        return sorted(results, key=lambda x: x["final_score"], reverse=True)

    @staticmethod
    def _compute_recency_score(year: Optional[int]) -> float:
        if year is None:
            return 0.0

        if config.MAX_YEAR == config.MIN_YEAR:
            return 1.0

        return (year - config.MIN_YEAR) / (config.MAX_YEAR - config.MIN_YEAR)