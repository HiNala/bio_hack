"""
RAG Schemas

Models for RAG synthesis endpoints.
"""

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Citation reference in RAG response."""
    index: int
    paper_id: str
    title: str
    authors: list[str]
    year: int | None = None


class RAGQueryRequest(BaseModel):
    """Request for RAG-powered answer."""
    query_id: str = Field(..., description="ID of the query with ingested papers")
    question: str = Field(..., min_length=5, max_length=2000)


class RAGResponse(BaseModel):
    """Synthesized answer from RAG pipeline."""
    query_id: str
    summary: str
    key_findings: list[str]
    consensus: list[str]
    open_questions: list[str]
    citations: list[Citation]
    papers_analyzed: int
