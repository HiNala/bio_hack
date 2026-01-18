"""
Ingest Schemas

Models for paper ingestion endpoints.
"""

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """Request to ingest papers for a query."""
    query_id: str = Field(..., description="ID of the analyzed query")


class IngestResponse(BaseModel):
    """Response from paper ingestion."""
    query_id: str
    papers_found: int
    papers_stored: int
    chunks_created: int = 0
    status: str
    message: str = ""
