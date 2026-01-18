"""
Paper Model

Represents academic papers/articles from literature sources.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, Boolean, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Paper(Base):
    """Academic paper or article."""

    __tablename__ = "papers"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Source reference
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id"),
        nullable=False,
    )

    # Ingest job reference (optional)
    ingest_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingest_jobs.id"),
        nullable=True,
        index=True,
    )

    # External identifiers
    external_id: Mapped[str] = mapped_column(String(500), nullable=False)
    doi: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)

    # Metadata
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authors: Mapped[list] = mapped_column(JSON, default=list)  # List of author names
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    venue: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Classification
    topics: Mapped[list] = mapped_column(JSON, default=list)  # List of topic/concept names
    fields_of_study: Mapped[list] = mapped_column(JSON, default=list)

    # Metrics
    citation_count: Mapped[int] = mapped_column(Integer, default=0)

    # URLs
    pdf_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    landing_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Processing status
    is_chunked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_embedded: Mapped[bool] = mapped_column(Boolean, default=False)

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
    source: Mapped["Source"] = relationship("Source", back_populates="papers")
    ingest_job: Mapped[Optional["IngestJob"]] = relationship("IngestJob", back_populates="papers")
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="paper",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_paper_source_external"),
    )

    def __repr__(self) -> str:
        return f"<Paper(title='{self.title[:50]}...', year={self.year})>"
