"""
User Settings Model

User preferences for retrieval, synthesis, and RAG.
"""

from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class UserSettings(Base):
    """User settings and preferences."""
    
    __tablename__ = "user_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Retrieval settings
    default_sources = Column(ARRAY(String), default=["openalex", "semantic_scholar"])
    papers_per_query = Column(Integer, default=50)
    min_citations = Column(Integer, default=0)
    year_from = Column(Integer, nullable=True)
    year_to = Column(Integer, nullable=True)
    
    # Synthesis settings
    synthesis_detail = Column(String(20), default="balanced")  # 'brief', 'balanced', 'detailed'
    max_sources_cited = Column(Integer, default=10)
    include_methodology = Column(Boolean, default=True)
    include_limitations = Column(Boolean, default=True)
    include_consensus = Column(Boolean, default=True)
    include_contested = Column(Boolean, default=True)
    
    # RAG settings
    chunks_per_query = Column(Integer, default=20)
    similarity_threshold = Column(Float, default=0.7)
    reranking_enabled = Column(Boolean, default=True)
    diversify_sources = Column(Boolean, default=True)
    
    # UI preferences
    theme = Column(String(20), default="light")
    sidebar_collapsed = Column(Boolean, default=False)
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('papers_per_query >= 10 AND papers_per_query <= 200', name='check_papers_per_query'),
        CheckConstraint('chunks_per_query >= 5 AND chunks_per_query <= 50', name='check_chunks_per_query'),
        CheckConstraint('similarity_threshold >= 0.5 AND similarity_threshold <= 0.95', name='check_similarity_threshold'),
    )
    
    # Relationships
    user = relationship("User", back_populates="settings")
    
    def __repr__(self):
        return f"<UserSettings user_id={self.user_id}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "default_sources": self.default_sources or ["openalex", "semantic_scholar"],
            "papers_per_query": self.papers_per_query or 50,
            "min_citations": self.min_citations or 0,
            "year_from": self.year_from,
            "year_to": self.year_to,
            "synthesis_detail": self.synthesis_detail or "balanced",
            "max_sources_cited": self.max_sources_cited or 10,
            "include_methodology": self.include_methodology,
            "include_limitations": self.include_limitations,
            "include_consensus": self.include_consensus,
            "include_contested": self.include_contested,
            "chunks_per_query": self.chunks_per_query or 20,
            "similarity_threshold": self.similarity_threshold or 0.7,
            "reranking_enabled": self.reranking_enabled,
            "diversify_sources": self.diversify_sources,
            "theme": self.theme or "light",
            "sidebar_collapsed": self.sidebar_collapsed,
        }
