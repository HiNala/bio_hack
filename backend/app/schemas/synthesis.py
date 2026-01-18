"""
Synthesis Schemas

Pydantic schemas for synthesis API requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Any, Dict, Union
from pydantic import BaseModel, Field
from uuid import UUID


class SynthesisRequest(BaseModel):
    """Request to generate a synthesis."""
    query: str = Field(..., min_length=5, max_length=2000)
    mode: str = Field(default="synthesize")  # 'synthesize', 'compare', 'plan', 'explore'
    workspace_id: Optional[UUID] = None
    collection_ids: Optional[List[UUID]] = None  # Restrict to specific collections
    
    # Override settings for this query
    settings_override: Optional[Dict[str, Any]] = None


class SourceReference(BaseModel):
    """Reference to a source paper used in synthesis."""
    citation_id: int  # [1], [2], etc.
    paper_id: UUID
    title: str
    authors: List[str]
    year: Optional[int]
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    citation_count: int = 0
    relevance_score: float
    chunks_used: int


class Finding(BaseModel):
    """A key finding with citations."""
    finding: str
    citations: List[int]
    confidence: str = "medium"  # 'high', 'medium', 'low'


class ConsensusPoint(BaseModel):
    """A point of scientific consensus."""
    point: str
    citations: List[int]


class Position(BaseModel):
    """A position in a contested topic."""
    position: str
    citations: List[int]


class ContestedTopic(BaseModel):
    """A topic where papers disagree."""
    topic: str
    positions: List[Position]


class SynthesizeContent(BaseModel):
    """Content structure for SYNTHESIZE mode."""
    executive_summary: str
    key_findings: List[Finding]
    consensus: List[ConsensusPoint]
    contested: List[ContestedTopic]
    limitations: List[str]
    suggested_readings: List[int]  # Citation IDs


class ApproachInfo(BaseModel):
    """Information about a compared approach."""
    name: str
    description: str
    key_papers: List[int]


class ComparisonCell(BaseModel):
    """A cell in the comparison table."""
    approach: str
    assessment: str
    citations: List[int]


class ComparisonRow(BaseModel):
    """A row in the comparison table."""
    category: str
    comparisons: List[ComparisonCell]


class StrengthWeakness(BaseModel):
    """A strength or weakness with citations."""
    point: str
    citations: List[int]


class ApproachAnalysis(BaseModel):
    """Analysis of a single approach."""
    approach: str
    strengths: List[StrengthWeakness]
    weaknesses: List[StrengthWeakness]


class Recommendation(BaseModel):
    """A use-case recommendation."""
    use_case: str
    recommended: str
    rationale: str


class CompareContent(BaseModel):
    """Content structure for COMPARE mode."""
    overview: str
    approaches: List[ApproachInfo]
    comparison_table: Dict[str, Any]  # categories and rows
    strengths_weaknesses: List[ApproachAnalysis]
    recommendations: List[Recommendation]


class EstablishedFinding(BaseModel):
    """A well-established finding."""
    finding: str
    citations: List[int]
    confidence: str = "high"


class ResearchGap(BaseModel):
    """An identified research gap."""
    gap: str
    evidence: str
    citations: List[int]
    impact_potential: str = "medium"  # 'high', 'medium', 'low'
    difficulty: str = "medium"


class PromisingDirection(BaseModel):
    """A promising research direction."""
    direction: str
    rationale: str
    related_work: List[int]
    suggested_approach: str


class PlanContent(BaseModel):
    """Content structure for PLAN mode."""
    field_overview: str
    well_established: List[EstablishedFinding]
    research_gaps: List[ResearchGap]
    promising_directions: List[PromisingDirection]
    suggested_research_questions: List[str]
    recommended_reading_order: List[int]


class ExploreContent(BaseModel):
    """Content structure for EXPLORE mode."""
    topic_focus: str
    detailed_explanation: str
    key_points: List[Finding]
    technical_details: Optional[str] = None
    related_concepts: List[str]
    further_reading: List[int]


class SynthesisResponse(BaseModel):
    """Complete synthesis response."""
    id: UUID
    mode: str
    query: str
    created_at: datetime
    
    # Sources
    sources: List[SourceReference]
    total_papers_analyzed: int
    total_chunks_used: int
    
    # Content (varies by mode)
    content: Dict[str, Any]  # Actual content depends on mode
    
    # Generation metadata
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    generation_time_ms: Optional[int] = None
    
    # Quality indicators
    confidence_score: Optional[float] = None
    coverage_warning: Optional[str] = None
    
    class Config:
        from_attributes = True


class SynthesisFeedback(BaseModel):
    """User feedback on a synthesis."""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class SavedQueryResponse(BaseModel):
    """Response for a saved query."""
    id: UUID
    workspace_id: UUID
    name: Optional[str]
    raw_query: str
    result_count: Optional[int]
    created_at: datetime
    last_run_at: Optional[datetime]
    
    class Config:
        from_attributes = True
