"""
Ingest Job Schemas

Request/response models for ingestion jobs.
"""

from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.progress import JobProgress


class IngestJobCreateRequest(BaseModel):
    query: str = Field(..., min_length=3)
    sources: Optional[List[str]] = None
    max_results_per_source: int = Field(50, ge=1, le=200)


class IngestJobCreateResponse(BaseModel):
    job_id: str
    status: str
    message: str


class IngestJobError(BaseModel):
    stage: str
    message: str
    recoverable: bool = True


class IngestJobResponse(BaseModel):
    job_id: str
    status: str
    original_query: str
    parsed_queries: Optional[dict] = None
    progress: Optional[JobProgress] = None
    elapsed_time_ms: Optional[int] = None
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[IngestJobError] = None


class IngestJobSummary(BaseModel):
    job_id: str
    status: str
    original_query: str
    papers_count: int
    created_at: str
    completed_at: Optional[str] = None


class IngestJobListResponse(BaseModel):
    jobs: List[IngestJobSummary]


class IngestJobPaper(BaseModel):
    id: str
    title: str
    authors: List[str]
    year: Optional[int] = None
    venue: Optional[str] = None
    citation_count: int = 0
    abstract_preview: Optional[str] = None
    chunk_count: int = 0
    is_embedded: bool = False
    doi: Optional[str] = None
    url: Optional[str] = None


class IngestJobPapersResponse(BaseModel):
    job_id: str
    total_papers: int
    papers: List[IngestJobPaper]
