"""
Research Memory Models

Models for persistent research context and session management.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON

from app.database import Base


class ResearchSession(Base):
    """Research session grouping related queries."""

    __tablename__ = "research_sessions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign keys
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Session identity
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Topic tracking
    primary_topic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    related_topics: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)

    # Session state
    status: Mapped[str] = mapped_column(String(20), default="active")  # 'active', 'paused', 'completed'

    # Aggregated context
    key_claims: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    key_papers: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    consensus_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="research_sessions")
    queries: Mapped[List["SessionQuery"]] = relationship(
        "SessionQuery",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    insights: Mapped[List["ResearchInsight"]] = relationship(
        "ResearchInsight",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    memory_summaries: Mapped[List["MemorySummary"]] = relationship(
        "MemorySummary",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ResearchSession(name='{self.name}', status='{self.status}')>"


class SessionQuery(Base):
    """Individual query within a research session."""

    __tablename__ = "session_queries"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign keys
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Query details
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'initial', 'followup', 'refinement', 'tangent'

    # Results
    synthesis_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("synthesis_results.id"),
        nullable=True,
    )
    claims_discovered: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    papers_used: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)

    # Context used
    prior_context_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Learning
    user_marked_useful: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    user_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    session: Mapped["ResearchSession"] = relationship("ResearchSession", back_populates="queries")
    synthesis: Mapped[Optional["SynthesisResult"]] = relationship("SynthesisResult", back_populates="session_queries")

    def __repr__(self) -> str:
        return f"<SessionQuery(query='{self.query_text[:50]}...', type='{self.query_type}')>"


class ResearchInsight(Base):
    """Accumulated learnings from research session."""

    __tablename__ = "research_insights"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign keys
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Insight details
    insight_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'finding', 'gap', 'contradiction', 'connection'
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Supporting evidence
    supporting_claims: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    supporting_papers: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)

    # User validation
    user_confirmed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    user_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    session: Mapped["ResearchSession"] = relationship("ResearchSession", back_populates="insights")

    def __repr__(self) -> str:
        return f"<ResearchInsight(type='{self.insight_type}', content='{self.content[:50]}...')>"


class MemorySummary(Base):
    """Compressed context summary for future use."""

    __tablename__ = "memory_summaries"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign keys
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Summary content
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    summary_embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)

    # What this summary covers
    query_ids: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    time_range_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    time_range_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    compression_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    session: Mapped["ResearchSession"] = relationship("ResearchSession", back_populates="memory_summaries")

    def __repr__(self) -> str:
        return f"<MemorySummary(session_id='{self.session_id}', tokens={self.token_count})>"