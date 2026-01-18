"""
Document Schemas

Models for paper/document endpoints.
"""

from typing import Optional
from pydantic import BaseModel


class PaperResponse(BaseModel):
    """Paper metadata response."""
    id: str
    title: str
    abstract: Optional[str] = None
    authors: list[str]
    year: Optional[int] = None
    venue: Optional[str] = None
    source: str
    citation_count: int
    doi: Optional[str] = None
    url: Optional[str] = None


class DocumentsResponse(BaseModel):
    """Response containing list of papers."""
    query_id: Optional[str] = None
    papers: list[PaperResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
