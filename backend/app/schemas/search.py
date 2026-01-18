"""
Search Schemas

Models for semantic search endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request for semantic search."""
    query: str = Field(..., min_length=3, max_length=1000)
    limit: int = Field(default=10, ge=1, le=100)


class SearchResult(BaseModel):
    """Single search result."""
    chunk_id: str
    paper_id: str
    paper_title: str
    text: str
    score: float


class SearchResponse(BaseModel):
    """Response from semantic search."""
    results: list[SearchResult]
    total: int
