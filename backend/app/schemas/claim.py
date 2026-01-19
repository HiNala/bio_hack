"""
Claim Schemas

Pydantic schemas for claim extraction, evidence mapping, and claim clusters.
"""

from datetime import datetime
from typing import Optional, List, Any, Dict, Union
from pydantic import BaseModel, Field
from uuid import UUID


class ClaimBase(BaseModel):
    """Base claim schema."""
    canonical_text: str
    normalized_text: str
    claim_type: str = Field(..., description="Type: 'finding', 'methodology', 'hypothesis', 'definition'")
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object: Optional[str] = None
    has_quantitative_data: bool = False
    effect_direction: Optional[str] = None  # 'positive', 'negative', 'neutral', 'mixed'
    effect_magnitude: Optional[str] = None
    domain_tags: List[str] = Field(default_factory=list)
    consensus_score: Optional[float] = None  # -1 to 1
    evidence_strength: float = 0.0  # 0-1


class ClaimCreate(BaseModel):
    """Schema for creating a new claim."""
    canonical_text: str
    normalized_text: str
    claim_type: str
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object: Optional[str] = None
    has_quantitative_data: bool = False
    effect_direction: Optional[str] = None
    effect_magnitude: Optional[str] = None
    domain_tags: List[str] = Field(default_factory=list)


class ClaimUpdate(BaseModel):
    """Schema for updating a claim."""
    canonical_text: Optional[str] = None
    domain_tags: Optional[List[str]] = None
    consensus_score: Optional[float] = None
    evidence_strength: Optional[float] = None


class ClaimResponse(ClaimBase):
    """Response schema for a claim."""
    id: UUID
    supporting_count: int = 0
    opposing_count: int = 0
    conditional_count: int = 0
    total_evidence_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvidenceBase(BaseModel):
    """Base evidence schema."""
    claim_id: UUID
    chunk_id: UUID
    paper_id: UUID
    stance: str = Field(..., description="Stance: 'supports', 'opposes', 'conditional', 'neutral'")
    confidence: float = Field(..., ge=0.0, le=1.0)
    relevant_quote: Optional[str] = None
    conditions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    methodology_type: Optional[str] = None
    sample_size: Optional[int] = None
    is_primary_source: Optional[bool] = None


class EvidenceCreate(BaseModel):
    """Schema for creating claim evidence."""
    claim_id: UUID
    chunk_id: UUID
    paper_id: UUID
    stance: str
    confidence: float
    relevant_quote: Optional[str] = None
    conditions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    methodology_type: Optional[str] = None
    sample_size: Optional[int] = None
    is_primary_source: Optional[bool] = None


class EvidenceResponse(EvidenceBase):
    """Response schema for claim evidence."""
    id: UUID
    extracted_at: datetime
    extraction_model: Optional[str] = None
    extraction_confidence: Optional[float] = None

    class Config:
        from_attributes = True


class EvidenceItem(BaseModel):
    """Evidence item for claim mapping."""
    paper_id: str
    paper_title: str
    paper_year: Optional[int] = None
    citation_count: int = 0
    quote: str = ""
    conditions: List[str] = Field(default_factory=list)
    confidence: float = 0.8


class ClaimEvidenceMap(BaseModel):
    """Full evidence map for a claim."""
    claim: ClaimResponse
    supporting: List[EvidenceItem] = Field(default_factory=list)
    opposing: List[EvidenceItem] = Field(default_factory=list)
    conditional: List[EvidenceItem] = Field(default_factory=list)
    consensus_score: float = 0.0  # -1 to 1
    evidence_strength: float = 0.0  # 0-1


class ClaimClusterBase(BaseModel):
    """Base claim cluster schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    canonical_claim_id: Optional[UUID] = None


class ClaimClusterCreate(BaseModel):
    """Schema for creating a claim cluster."""
    name: Optional[str] = None
    description: Optional[str] = None
    claim_ids: List[UUID] = Field(default_factory=list)


class ClaimClusterResponse(ClaimClusterBase):
    """Response schema for a claim cluster."""
    id: UUID
    claim_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ClaimClusterMember(BaseModel):
    """Claim cluster membership."""
    cluster_id: UUID
    claim_id: UUID
    similarity_score: Optional[float] = None


class ClaimExtractionRequest(BaseModel):
    """Request to extract claims from chunks."""
    chunk_ids: List[UUID] = Field(..., min_items=1)
    paper_id: UUID


class ClaimExtractionResponse(BaseModel):
    """Response from claim extraction."""
    claims: List[ClaimResponse] = Field(default_factory=list)
    evidence_links: List[EvidenceResponse] = Field(default_factory=list)
    processing_time_ms: int


class ClaimSearchRequest(BaseModel):
    """Request to search for claims."""
    query: str
    domain_filter: Optional[List[str]] = None
    claim_type_filter: Optional[List[str]] = None
    min_evidence_strength: float = 0.0
    limit: int = 50


class ClaimSearchResponse(BaseModel):
    """Response from claim search."""
    claims: List[ClaimResponse] = Field(default_factory=list)
    total_count: int
    search_time_ms: int


class ClaimClusteringRequest(BaseModel):
    """Request to cluster claims."""
    claim_ids: List[UUID] = Field(..., min_items=2)
    similarity_threshold: float = 0.8


class ClaimClusteringResponse(BaseModel):
    """Response from claim clustering."""
    clusters: List[ClaimClusterResponse] = Field(default_factory=list)
    unclustered_claims: List[UUID] = Field(default_factory=list)
    processing_time_ms: int