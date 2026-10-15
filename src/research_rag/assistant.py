from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src import config
from src.retriever import ResearchPaperRetriever


class ResearchRAGAssistant:
    """
    Handles user-facing RAG interaction:
    - receives a research query
    - retrieves relevant papers
    - builds grounded context
    - calls the LLM
    - returns answer + citations
    """
    
    def __init__(self, retriever: ResearchPaperRetriever, llm: Optional[Any] = None) -> None:
        self.retriever = retriever
        self.llm = llm or ChatOllama(
            model=config.RAG_MODEL,
            temperature=config.LLM_TEMPERATURE,
            num_ctx=config.LLM_CONTEXT_WINDOW
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", config.SYSTEM_PROMPT),
            ("human", "User question: {query}\n\nRetrieved paper context: {context}\n\nAnswer:\n")
        ])

    def answer(
        self, query: str, 
        k: int = config.K, 
        fetch_k: int = config.FETCH_K, 
        rerank: bool = True, 
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a grounded answer from retrieved research papers.
        """
        retrieved_papers = self.retriever.retrieve(
            query=query,
            k=k,
            fetch_k=fetch_k,
            rerank=rerank
        )

        filtered_papers = [r for r in retrieved_papers if r["vector_score"] >= config.MIN_VECTOR_SCORE]
        if len(filtered_papers) < config.MIN_RESULTS_AFTER_FILTER:
            filtered_papers = retrieved_papers[:config.MIN_RESULTS_AFTER_FILTER]

        if not filtered_papers:
            return {
                "query": query,
                "answer": "I could not find relevant papers about this topic in the current ArXiv corpus.",
                "sources": []
            }

        context = self._build_context(filtered_papers)

        chain = self.prompt | self.llm
        response = chain.invoke({
            "query": query,
            "context": context
        })

        answer_text = self._extract_text(response)

        result = {
            "query": query,
            "answer": answer_text
        }

        if include_sources:
            result["sources"] = self._format_sources(retrieved_papers)

        return result

    def _build_context(self, papers: List[Dict[str, Any]]) -> str:
        """
        Build context blocks for the LLM.
        """
        context_blocks = []

        for i, paper in enumerate(papers, start=1):
            title = paper.get("title", "Unknown title")
            year = paper.get("year", "Unknown year")
            doc_id = paper.get("id", "Unknown ID")
            is_published = paper.get("is_published", False)
            content = paper.get("content", "")
            publication_status = "pusblished" if is_published else "preprint"

            block = f"""
            [{i}]
            Title: {title}
            arXiv ID: {doc_id}
            Publication status: {publication_status}

            Content:
            {content}
            """.strip()

            context_blocks.append(block)

        return "\n\n---\n\n".join(context_blocks)

    def _format_sources(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Return structured source metadata for UI/debugging.
        """
        sources = []

        for i, paper in enumerate(papers, start=1):
            sources.append({
                "citation_number": i,
                "doc_id": paper.get("id"),
                "title": paper.get("title"),
                "year": paper.get("year"),
                "is_published": paper.get("is_published"),
                "vector_score": paper.get("vector_score"),
                "recency_score": paper.get("recency_score"),
                "publication_score": paper.get("publication_score"),
                "final_score": paper.get("final_score")
            })

        return sources

    @staticmethod
    def _extract_text(response: Any) -> str:
        """
        Extract text from LangChain model response.
        """
        if hasattr(response, "content"):
            return response.content
        return str(response)