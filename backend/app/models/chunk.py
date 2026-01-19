"""
Chunk Model

Represents text chunks from papers for RAG retrieval.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from app.database import Base
from app.config import get_settings

settings = get_settings()


class Chunk(Base):
    """Text chunk from a paper for embedding and retrieval."""

    __tablename__ = "chunks"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Paper reference
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Chunk content
    text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Size metrics
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Vector embedding (1536 dimensions for text-embedding-3-small)
    embedding: Mapped[Optional[list]] = mapped_column(
        Vector(settings.embedding_dimensions),
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="chunks")
    claim_evidence: Mapped[list["ClaimEvidence"]] = relationship(
        "ClaimEvidence",
        back_populates="chunk",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Chunk(paper_id='{self.paper_id}', index={self.chunk_index})>"
