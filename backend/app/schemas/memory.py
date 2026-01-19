"""
Research Memory Schemas

Pydantic schemas for research sessions, insights, and memory summaries.
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from uuid import UUID


class ResearchSessionBase(BaseModel):
    """Base research session schema."""
    workspace_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    primary_topic: Optional[str] = None
    related_topics: List[str] = Field(default_factory=list)
    status: str = "active"  # 'active', 'paused', 'completed'


class ResearchSessionCreate(BaseModel):
    """Schema for creating a research session."""
    workspace_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    primary_topic: Optional[str] = None
    related_topics: List[str] = Field(default_factory=list)


class ResearchSessionUpdate(BaseModel):
    """Schema for updating a research session."""
    name: Optional[str] = None
    description: Optional[str] = None
    primary_topic: Optional[str] = None
    related_topics: Optional[List[str]] = None
    status: Optional[str] = None


class ResearchSessionResponse(ResearchSessionBase):
    """Response schema for a research session."""
    id: UUID
    key_claims: List[UUID] = Field(default_factory=list)
    key_papers: List[UUID] = Field(default_factory=list)
    consensus_snapshot: Optional[Dict[str, Any]] = None
    created_at: datetime
    last_activity_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionQueryBase(BaseModel):
    """Base session query schema."""
    session_id: UUID
    query_text: str
    query_type: Optional[str] = None  # 'initial', 'followup', 'refinement', 'tangent'
    synthesis_id: Optional[UUID] = None
    claims_discovered: List[UUID] = Field(default_factory=list)
    papers_used: List[UUID] = Field(default_factory=list)
    prior_context_used: Optional[str] = None
    context_relevance_score: Optional[float] = None
    user_marked_useful: Optional[bool] = None
    user_notes: Optional[str] = None


class SessionQueryCreate(BaseModel):
    """Schema for creating a session query."""
    session_id: UUID
    query_text: str
    query_type: Optional[str] = None
    synthesis_id: Optional[UUID] = None
    claims_discovered: List[UUID] = Field(default_factory=list)
    papers_used: List[UUID] = Field(default_factory=list)
    prior_context_used: Optional[str] = None
    context_relevance_score: Optional[float] = None


class SessionQueryResponse(SessionQueryBase):
    """Response schema for a session query."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchInsightBase(BaseModel):
    """Base research insight schema."""
    session_id: UUID
    insight_type: Optional[str] = None  # 'finding', 'gap', 'contradiction', 'connection'
    content: str
    supporting_claims: List[UUID] = Field(default_factory=list)
    supporting_papers: List[UUID] = Field(default_factory=list)
    user_confirmed: Optional[bool] = None
    user_notes: Optional[str] = None


class ResearchInsightCreate(BaseModel):
    """Schema for creating a research insight."""
    session_id: UUID
    insight_type: Optional[str] = None
    content: str
    supporting_claims: List[UUID] = Field(default_factory=list)
    supporting_papers: List[UUID] = Field(default_factory=list)


class ResearchInsightUpdate(BaseModel):
    """Schema for updating a research insight."""
    user_confirmed: Optional[bool] = None
    user_notes: Optional[str] = None


class ResearchInsightResponse(ResearchInsightBase):
    """Response schema for a research insight."""
    id: UUID
    discovered_at: datetime

    class Config:
        from_attributes = True


class MemorySummaryBase(BaseModel):
    """Base memory summary schema."""
    session_id: UUID
    summary_text: str
    query_ids: List[UUID] = Field(default_factory=list)
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    token_count: Optional[int] = None
    compression_ratio: Optional[float] = None


class MemorySummaryResponse(MemorySummaryBase):
    """Response schema for a memory summary."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchContext(BaseModel):
    """Context retrieved from research memory."""
    session_id: str
    context_text: str
    token_count: int
    sources: Dict[str, int]  # counts by source type


class TimelineEvent(BaseModel):
    """An event in the research timeline."""
    type: str  # 'query', 'insight'
    timestamp: datetime
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionTimeline(BaseModel):
    """Timeline of research session events."""
    session: ResearchSessionResponse
    events: List[TimelineEvent] = Field(default_factory=list)
    total_queries: int = 0
    total_insights: int = 0


class SessionDetectionRequest(BaseModel):
    """Request to get or create a research session."""
    workspace_id: UUID
    query: str = Field(..., min_length=5, max_length=2000)


class SessionDetectionResponse(BaseModel):
    """Response from session detection."""
    session: ResearchSessionResponse
    is_new: bool
    context_available: bool
    similar_sessions_found: int


class ContextRetrievalRequest(BaseModel):
    """Request to retrieve research context."""
    session_id: UUID
    current_query: str
    max_tokens: int = 2000


class ContextRetrievalResponse(BaseModel):
    """Response with retrieved context."""
    context: ResearchContext
    retrieval_time_ms: int


class SessionTimelineRequest(BaseModel):
    """Request to get session timeline."""
    session_id: UUID
    include_details: bool = True


class SessionTimelineResponse(BaseModel):
    """Response with session timeline."""
    timeline: SessionTimeline
    retrieval_time_ms: int


class MemoryStats(BaseModel):
    """Statistics about research memory usage."""
    total_sessions: int
    active_sessions: int
    total_queries: int
    total_insights: int
    total_memory_summaries: int
    average_session_duration_days: float
    most_active_workspace: Optional[UUID] = None