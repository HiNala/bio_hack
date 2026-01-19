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
from app.schemas.user import (
    UserCreate,
    UserResponse,
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
    CollectionPaperAdd,
    CollectionPaperUpdate,
    CollectionPaperResponse,
)
from app.schemas.settings import (
    SettingsUpdate,
    SettingsResponse,
    DEFAULT_SETTINGS,
)
from app.schemas.synthesis import (
    SynthesisRequest,
    SynthesisResponse,
    SynthesisFeedback,
    SourceReference,
    SavedQueryResponse,
)
from app.schemas.claim import (
    ClaimResponse,
    ClaimEvidenceMap,
    ClaimExtractionRequest,
    ClaimExtractionResponse,
    ClaimSearchRequest,
    ClaimSearchResponse,
)
from app.schemas.contradiction import (
    ContradictionResponse,
    ConsensusReport,
    ConsensusReportRequest,
    ConsensusReportResponse,
)
from app.schemas.memory import (
    ResearchSessionResponse,
    SessionTimeline,
    SessionDetectionRequest,
    SessionDetectionResponse,
    ContextRetrievalRequest,
    ContextRetrievalResponse,
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
    # User & Workspace
    "UserCreate",
    "UserResponse",
    "WorkspaceCreate",
    "WorkspaceUpdate",
    "WorkspaceResponse",
    "CollectionCreate",
    "CollectionUpdate",
    "CollectionResponse",
    "CollectionPaperAdd",
    "CollectionPaperUpdate",
    "CollectionPaperResponse",
    # Settings
    "SettingsUpdate",
    "SettingsResponse",
    "DEFAULT_SETTINGS",
    # Synthesis
    "SynthesisRequest",
    "SynthesisResponse",
    "SynthesisFeedback",
    "SourceReference",
    "SavedQueryResponse",
    # Core Intelligence
    "ClaimResponse",
    "ClaimEvidenceMap",
    "ClaimExtractionRequest",
    "ClaimExtractionResponse",
    "ClaimSearchRequest",
    "ClaimSearchResponse",
    "ContradictionResponse",
    "ConsensusReport",
    "ConsensusReportRequest",
    "ConsensusReportResponse",
    "ResearchSessionResponse",
    "SessionTimeline",
    "SessionDetectionRequest",
    "SessionDetectionResponse",
    "ContextRetrievalRequest",
    "ContextRetrievalResponse",
]
