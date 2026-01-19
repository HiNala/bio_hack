"""
Synthesis Result Model

Stores AI-generated synthesis results for research queries.
"""

from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class SynthesisResult(Base):
    """AI-generated synthesis result."""
    
    __tablename__ = "synthesis_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    query_id = Column(UUID(as_uuid=True), ForeignKey("saved_queries.id", ondelete="SET NULL"), nullable=True)
    
    # Mode & input
    mode = Column(String(50), nullable=False)  # 'synthesize', 'compare', 'plan', 'explore'
    input_query = Column(Text, nullable=False)
    
    # Sources used
    source_papers = Column(ARRAY(UUID(as_uuid=True)), nullable=True)  # Paper IDs used
    source_chunks = Column(ARRAY(UUID(as_uuid=True)), nullable=True)  # Chunk IDs used
    
    # Generated content
    content = Column(JSONB, nullable=False)  # Structured synthesis output
    
    # Source references (for display)
    sources_metadata = Column(JSONB, nullable=True)  # Metadata about cited sources
    
    # Metadata
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    generation_time_ms = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # User feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    user_feedback = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="synthesis_results")
    session_queries = relationship("SessionQuery", back_populates="synthesis", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SynthesisResult {self.mode}: {self.input_query[:30]}>"
