"""
Query Schemas

Models for query analysis endpoints.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class ParsedQuery(BaseModel):
    """Structured interpretation of a natural language query."""
    primary_terms: list[str] = Field(default_factory=list)
    expanded_terms: list[str] = Field(default_factory=list)
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    fields: list[str] = Field(default_factory=list)
    query_type: Literal["factual", "synthesis", "comparison", "survey"] = "synthesis"


class AnalyzeRequest(BaseModel):
    """Request to analyze a natural language query."""
    query: str = Field(..., min_length=5, max_length=2000)


class AnalyzeResponse(BaseModel):
    """Response from query analysis."""
    query_id: str
    parsed_query: ParsedQuery
    status: str
