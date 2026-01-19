"""
Contradiction Schemas

Pydantic schemas for contradiction detection and consensus analysis.
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from uuid import UUID

from app.schemas.claim import ClaimResponse, EvidenceItem


class ContradictionBase(BaseModel):
    """Base contradiction schema."""
    claim_id: UUID
    contradiction_type: str = Field(..., description="Type: methodological, population, temporal, definitional, statistical, scope")
    severity: float = Field(..., ge=0.0, le=1.0)
    evidence_a_id: Optional[UUID] = None
    evidence_b_id: Optional[UUID] = None
    explanation: Optional[str] = None
    resolution_suggestion: Optional[str] = None
    paper_a_id: Optional[UUID] = None
    paper_b_id: Optional[UUID] = None


class ContradictionCreate(BaseModel):
    """Schema for creating a contradiction."""
    claim_id: UUID
    contradiction_type: str
    severity: float
    evidence_a_id: Optional[UUID] = None
    evidence_b_id: Optional[UUID] = None
    explanation: Optional[str] = None
    resolution_suggestion: Optional[str] = None
    paper_a_id: Optional[UUID] = None
    paper_b_id: Optional[UUID] = None


class ContradictionResponse(ContradictionBase):
    """Response schema for a contradiction."""
    id: UUID
    detected_at: datetime

    class Config:
        from_attributes = True


class ConsensusItem(BaseModel):
    """A claim with strong consensus."""
    claim: ClaimResponse
    score: float  # consensus score -1 to 1
    evidence_count: int
    key_papers: List[str]  # paper IDs


class ContestedItem(BaseModel):
    """A claim with active contradictions."""
    claim: ClaimResponse
    contradictions: List[ContradictionResponse] = Field(default_factory=list)
    severity: float  # max contradiction severity


class ConditionalItem(BaseModel):
    """A claim with conditional evidence."""
    claim: ClaimResponse
    conditions: List[str] = Field(default_factory=list)


class ConsensusReport(BaseModel):
    """Report on consensus and contradictions for a topic."""
    topic: str
    consensus: List[ConsensusItem] = Field(default_factory=list)
    contested: List[ContestedItem] = Field(default_factory=list)
    conditional: List[ConditionalItem] = Field(default_factory=list)
    overall_consensus_score: float = 0.0  # -1 to 1


class ContradictionAnalysisRequest(BaseModel):
    """Request to analyze contradictions for a claim."""
    claim_id: UUID


class ContradictionAnalysisResponse(BaseModel):
    """Response from contradiction analysis."""
    claim_id: UUID
    contradictions: List[ContradictionResponse] = Field(default_factory=list)
    evidence_map: Dict[str, Any]  # simplified evidence map
    consensus_score: float = 0.0
    analysis_time_ms: int


class ConsensusReportRequest(BaseModel):
    """Request to generate a consensus report."""
    topic: str
    workspace_id: Optional[UUID] = None
    min_evidence_threshold: int = 1  # minimum evidence items to include


class ConsensusReportResponse(BaseModel):
    """Response with consensus report."""
    report: ConsensusReport
    generation_time_ms: int
    claims_analyzed: int
    papers_covered: int


class ContradictionDetectionRequest(BaseModel):
    """Request to detect contradictions across multiple claims."""
    claim_ids: List[UUID] = Field(..., min_items=1)
    workspace_id: Optional[UUID] = None


class ContradictionDetectionResponse(BaseModel):
    """Response from contradiction detection."""
    contradictions: List[ContradictionResponse] = Field(default_factory=list)
    claims_analyzed: int
    pairs_compared: int
    detection_time_ms: int


class DisagreementTypeAnalysis(BaseModel):
    """Analysis of a specific type of disagreement."""
    type: str  # methodological, population, etc.
    count: int
    average_severity: float
    examples: List[ContradictionResponse] = Field(default_factory=list)


class DisagreementSummary(BaseModel):
    """Summary of disagreements in a topic area."""
    total_contradictions: int
    by_type: List[DisagreementTypeAnalysis] = Field(default_factory=list)
    most_contested_claims: List[ContestedItem] = Field(default_factory=list)
    resolution_opportunities: List[Dict[str, Any]] = Field(default_factory=list)