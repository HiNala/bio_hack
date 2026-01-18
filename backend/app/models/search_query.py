"""
SearchQuery Model

Tracks user queries and their parsed interpretations.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class SearchQuery(Base):
    """User search query with parsed interpretation."""

    __tablename__ = "search_queries"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Original query
    raw_query: Mapped[str] = mapped_column(Text, nullable=False)

    # Parsed interpretation
    parsed_query: Mapped[dict] = mapped_column(JSON, default=dict)
    # Structure:
    # {
    #     "primary_terms": ["term1", "term2"],
    #     "expanded_terms": ["synonym1", "related1"],
    #     "year_from": 2010,
    #     "year_to": 2024,
    #     "fields": ["Physics", "Chemistry"],
    #     "query_type": "synthesis"
    # }

    # Processing status
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )
    # Status values: pending, parsing, ingesting, embedding, ready, failed

    # Results summary
    papers_found: Mapped[Optional[int]] = mapped_column(nullable=True)
    papers_embedded: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<SearchQuery(query='{self.raw_query[:50]}...', status='{self.status}')>"
