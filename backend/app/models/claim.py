"""
Claim Models

Models for claim extraction, evidence mapping, and claim clustering.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, DateTime, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.database import Base


class Claim(Base):
    """Scientific claim extracted from papers."""

    __tablename__ = "claims"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Canonical claim
    canonical_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Structure
    claim_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'finding', 'methodology', 'hypothesis', 'definition'
    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    predicate: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    object: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Quantitative data (if applicable)
    has_quantitative_data: Mapped[bool] = mapped_column(Boolean, default=False)
    effect_direction: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 'positive', 'negative', 'neutral', 'mixed'
    effect_magnitude: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Classification
    domain_tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # Embedding for similarity search (using pgvector)
    embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)

    # Aggregated metrics (updated by triggers)
    supporting_count: Mapped[int] = mapped_column(Integer, default=0)
    opposing_count: Mapped[int] = mapped_column(Integer, default=0)
    conditional_count: Mapped[int] = mapped_column(Integer, default=0)
    total_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    consensus_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # -1 (contested) to 1 (consensus)
    evidence_strength: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-1 based on citation quality

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    evidence: Mapped[List["ClaimEvidence"]] = relationship(
        "ClaimEvidence",
        back_populates="claim",
        cascade="all, delete-orphan",
    )
    contradictions: Mapped[List["Contradiction"]] = relationship(
        "Contradiction",
        back_populates="claim",
        cascade="all, delete-orphan",
    )
    cluster_memberships: Mapped[List["ClaimClusterMember"]] = relationship(
        "ClaimClusterMember",
        back_populates="claim",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Claim(type='{self.claim_type}', text='{self.canonical_text[:50]}...')>"


class ClaimEvidence(Base):
    """Evidence linking a claim to a source chunk/paper."""

    __tablename__ = "claim_evidence"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign keys
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chunks.id", ondelete="CASCADE"),
        nullable=False,
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Evidence relationship
    stance: Mapped[str] = mapped_column(String(20), nullable=False)  # 'supports', 'opposes', 'conditional', 'neutral'
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Context
    relevant_quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conditions: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    limitations: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)

    # Source quality indicators
    methodology_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'rct', 'observational', 'meta-analysis', etc.
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_primary_source: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)  # Original research vs review

    # Extraction metadata
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    extraction_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extraction_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="evidence")
    chunk: Mapped["Chunk"] = relationship("Chunk", back_populates="claim_evidence")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="claim_evidence")

    # Constraints
    __table_args__ = (
        UniqueConstraint("claim_id", "chunk_id", name="uq_claim_chunk"),
    )

    def __repr__(self) -> str:
        return f"<ClaimEvidence(claim_id='{self.claim_id}', stance='{self.stance}', confidence={self.confidence})>"


class ClaimCluster(Base):
    """Group of semantically similar claims."""

    __tablename__ = "claim_clusters"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Cluster identity
    name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Representative claim
    canonical_claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id"),
        nullable=True,
    )

    # Metadata
    claim_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    canonical_claim: Mapped[Optional["Claim"]] = relationship("Claim")
    members: Mapped[List["ClaimClusterMember"]] = relationship(
        "ClaimClusterMember",
        back_populates="cluster",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ClaimCluster(name='{self.name}', count={self.claim_count})>"


class ClaimClusterMember(Base):
    """Junction table for claim cluster membership."""

    __tablename__ = "claim_cluster_members"

    # Composite primary key
    cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claim_clusters.id", ondelete="CASCADE"),
        primary_key=True,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Membership metadata
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    cluster: Mapped["ClaimCluster"] = relationship("ClaimCluster", back_populates="members")
    claim: Mapped["Claim"] = relationship("Claim", back_populates="cluster_memberships")

    def __repr__(self) -> str:
        return f"<ClaimClusterMember(cluster_id='{self.cluster_id}', claim_id='{self.claim_id}')>"


class Contradiction(Base):
    """Detected contradiction between evidence for a claim."""

    __tablename__ = "contradictions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # The claim being contested
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Contradiction details
    contradiction_type: Mapped[str] = mapped_column(String(50), nullable=False)  # methodological, population, temporal, etc.
    severity: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1, how significant is this disagreement

    # The conflicting evidence
    evidence_a_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claim_evidence.id"),
        nullable=True,
    )
    evidence_b_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claim_evidence.id"),
        nullable=True,
    )

    # Analysis
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Papers involved
    paper_a_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id"),
        nullable=True,
    )
    paper_b_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id"),
        nullable=True,
    )

    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="contradictions")
    evidence_a: Mapped[Optional["ClaimEvidence"]] = relationship("ClaimEvidence", foreign_keys=[evidence_a_id])
    evidence_b: Mapped[Optional["ClaimEvidence"]] = relationship("ClaimEvidence", foreign_keys=[evidence_b_id])
    paper_a: Mapped[Optional["Paper"]] = relationship("Paper", foreign_keys=[paper_a_id])
    paper_b: Mapped[Optional["Paper"]] = relationship("Paper", foreign_keys=[paper_b_id])

    # Constraints
    __table_args__ = (
        UniqueConstraint("claim_id", "evidence_a_id", "evidence_b_id", name="uq_contradiction_evidence"),
    )

    def __repr__(self) -> str:
        return f"<Contradiction(claim_id='{self.claim_id}', type='{self.contradiction_type}', severity={self.severity})>"