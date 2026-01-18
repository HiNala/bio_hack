"""
Pydantic Schemas

Request/response models for API endpoints.
"""

from app.schemas.common import HealthResponse
from app.schemas.query import (
    AnalyzeRequest,
    AnalyzeResponse,
    ParsedQuery,
)
from app.schemas.ingest import IngestRequest, IngestResponse
from app.schemas.ingest_job import (
    IngestJobCreateRequest,
    IngestJobCreateResponse,
    IngestJobResponse,
    IngestJobListResponse,
    IngestJobPapersResponse,
)
from app.schemas.progress import JobProgress
from app.schemas.document import (
    PaperResponse,
    DocumentsResponse,
)
from app.schemas.search import (
    SearchRequest,
    SearchResult,
    SearchResponse,
)
from app.schemas.rag import (
    RAGQueryRequest,
    RAGResponse,
    Citation,
)

__all__ = [
    "HealthResponse",
    "AnalyzeRequest",
    "AnalyzeResponse",
    "ParsedQuery",
    "IngestRequest",
    "IngestResponse",
    "IngestJobCreateRequest",
    "IngestJobCreateResponse",
    "IngestJobResponse",
    "IngestJobListResponse",
    "IngestJobPapersResponse",
    "JobProgress",
    "PaperResponse",
    "DocumentsResponse",
    "SearchRequest",
    "SearchResult",
    "SearchResponse",
    "RAGQueryRequest",
    "RAGResponse",
    "Citation",
]
